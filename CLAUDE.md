# UniTrack — CLAUDE.md

A local Flask + SQLite task tracker for a Computer Engineering student managing coursework and internship applications. Pink-themed UI with an inbox-first workflow (capture now, organize later).

---

## Project Structure

```
UniTrack/
├── app/
│   ├── __init__.py        # create_app() factory — wires config, db, routes
│   ├── config.py          # DevelopmentConfig / ProductionConfig
│   ├── database.py        # All SQLite operations (Database class)
│   └── routes.py          # All Flask routes via register_routes(app, db)
├── static/
│   ├── css/style.css      # Entire pink theme — single file, CSS variables at top
│   └── js/                # Empty — placeholder for future JS
├── templates/
│   ├── base.html          # Navbar + flash messages + content block
│   ├── dashboard.html     # Main view — tasks grouped by course
│   ├── calendar.html      # Monthly calendar view
│   ├── tasks/
│   │   ├── add_quick_note.html   # Single-field inbox dump
│   │   ├── process_inbox.html    # Bulk process inbox items
│   │   └── edit_task.html        # Full task editor
│   └── courses/
│       └── add_course.html
├── cli.py                 # Rich-powered terminal interface (mirrors web app)
├── run.py                 # Dev entry point: python run.py
├── wsgi.py                # Production entry point for gunicorn/uWSGI
├── .env                   # NOT committed — copy from .env.example
├── .env.example           # Committed template for env vars
└── requirements.txt       # Flask, python-dotenv, rich
```

**How to run locally:**
```bash
pip install -r requirements.txt
python run.py
# → http://localhost:5000
```

---

## Database Schema

Two tables in `unitrack.db` (SQLite, auto-created on first run):

```
courses: id, name (UNIQUE)
tasks:   id, title, course_id (FK→courses, nullable), due_date (TEXT YYYY-MM-DD),
         status (Inbox|Pending), created_at (ISO timestamp), description (nullable)
```

**Task lifecycle (current):** Inbox → Pending *(stuck — no Done state)*

**Task lifecycle (target):** Inbox → Pending → Done, with delete capability

The `Database` class in `app/database.py` is the only place that touches SQL. All queries use parameterized statements. To add a new query, add a method there; don't write SQL in routes.

---

## Issues to Fix — Ordered by Priority

### DEPLOYMENT BLOCKERS (must fix before any public URL)

1. **Secret key** — `.env` has placeholder `your-secret-key-here`. Generate a real one:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Set it in `.env` and in the hosting platform's env vars. `wsgi.py` uses `ProductionConfig` which reads only from `os.environ`.

2. **Remove `.env` from git history** — it was committed in the initial commit. After setting a real key, run:
   ```bash
   git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" HEAD
   ```
   Then push with `--force`. Rotate the secret key after cleaning history.

3. **Add `gunicorn` to requirements** for production serving:
   ```
   gunicorn>=21.0.0
   ```
   Production start command: `gunicorn wsgi:app`

4. **Database persistence on deployment** — SQLite writes to local disk. On ephemeral platforms (Render free tier, Railway ephemeral), the file resets on redeploy. Options:
   - Use a persistent disk/volume mount (Render paid, Railway volumes)
   - Migrate to PostgreSQL (bigger lift — see future plans)
   - Use Railway or Fly.io with a persistent volume pointing to `/data/unitrack.db` and set `DATABASE_PATH=/data/unitrack.db`

### UI/UX — HIGH IMPACT

5. **No way to complete or delete tasks** — biggest workflow gap. Tasks go Inbox → Pending and stay forever.
   - Add `POST /complete-task/<id>` → calls `db.update_task(task_id, status='Done')`
   - Add `POST /delete-task/<id>` → new `db.delete_task(task_id)` method
   - Add complete/delete buttons to `dashboard.html` task cards and `edit_task.html`
   - Dashboard should only show `Pending` tasks (already does), but add a "Completed" section or separate view

6. **Mobile navbar breaks** — `nav-menu` wraps awkwardly below ~480px. The `@media (max-width: 768px)` block in `style.css` handles wrapping but nav items are still too crowded. Either:
   - Shorten link labels ("Quick Note" → "Inbox+", "Process Inbox" → "Process")
   - Add a hamburger menu toggle (small JS, ~10 lines)

7. **Calendar overflows on mobile** — cells are too small below 600px. The calendar grid needs a horizontal scroll wrapper on mobile. Added a `min-width: 560px` on weekday/week rows in the CSS (line ~375) — verify this renders correctly.

8. **Task ID shown to users** — `dashboard.html` line 48/77 shows `ID: {{ task.id }}`. Remove it. IDs are internal.

9. **`created_at` raw ISO string in edit form** — `edit_task.html` now trims to `[:10]` (date only). Looks cleaner.

10. **Flash message on quick note add** — currently shows task ID in the message. Routes already fixed to just say "Task added to Inbox!" — no ID leak.

### UI/UX — MEDIUM IMPACT

11. **No task status toggle on dashboard** — add a small "Mark Done" button (✓) per task card. Use a quick `<form>` POST to `/complete-task/<id>`. No JavaScript needed.

12. **Dashboard tasks not sorted by due date within course groups** — the DB query in `database.py` already sorts by `due_date IS NULL, due_date` but the dashboard groups them in Python dict order. Sort each group by due date after grouping in `routes.py`.

13. **Calendar `max-height: 80px` on task list clips tasks silently** (`style.css` line ~368). Either remove the cap or add a "+N more" indicator when tasks overflow.

14. **`process_inbox.html` created_at is raw ISO** — format it to `YYYY-MM-DD` in the template: `{{ item.created_at[:10] }}`.

15. **No CSRF protection** — forms are vulnerable to cross-site request forgery. Install `flask-wtf` and enable CSRF globally, or use the manual `itsdangerous` token approach. Low risk for a local/single-user app but required before any public deployment.

### MISSING FEATURES (add in this order)

16. **Complete/Delete tasks** — see item 5 above (highest priority feature)
17. **Task status filter on dashboard** — toggle to show Done tasks
18. **Course management page** — list courses, allow rename/delete
19. **Search** — simple title search across tasks
20. **Priority field** — Low/Medium/High on tasks (DB migration needed: `ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Medium'`)

---

## Task Management Analysis

**Current model problems:**
- Status only has `Inbox` and `Pending` — no completion state
- `update_task()` in `database.py` skips `None` values, so `course_id=None` can't clear a course (the `if course_id is not None` check means `None` is treated as "don't update"). To allow clearing a course, the routes currently pass `course_id=None` through `update_task_from_inbox` which sets it directly in SQL — that works. But `update_task()` can't clear a field to NULL because `None` means "skip". **Fix:** add a sentinel value or separate `clear_course()` method.
- No `deleted_at` / soft delete — deleting data permanently is fine for this use case, just add a `DELETE FROM tasks WHERE id = ?` method.

**Recommended schema additions (one migration):**
```sql
ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Medium';  -- Low/Medium/High
```
And add a `Done` status to the existing status field (no migration needed, just start using it in routes).

**Better `update_task()` signature** — current dynamic builder skips `None`. Use a sentinel to distinguish "don't change" from "set to NULL":
```python
_UNSET = object()

def update_task(self, task_id, title=_UNSET, course_id=_UNSET, ...):
    if course_id is not _UNSET:
        updates.append("course_id = ?")
        params.append(course_id)  # None is now valid (clears course)
```

---

## Deployment Guide

### Recommended platform: **Railway** (easiest for SQLite + Flask)

1. Push to GitHub
2. Connect repo to Railway → New Project → Deploy from GitHub
3. Set env vars in Railway dashboard:
   - `SECRET_KEY` = (generated 32-char hex)
   - `FLASK_ENV` = `production`
   - `DATABASE_PATH` = `/data/unitrack.db`
4. Add a Railway volume mounted at `/data`
5. Railway auto-detects Python; set start command to `gunicorn wsgi:app`

### Alternative: **Render** (free tier, but ephemeral disk on free)
- Use a Render Disk ($7/mo) for SQLite persistence
- Or switch to Render's free PostgreSQL (requires database.py rewrite to use `psycopg2`)

### Alternative: **Fly.io**
- `fly launch` → auto-detects Flask
- Add a persistent volume: `fly volumes create unitrack_data --size 1`
- Set `DATABASE_PATH=/data/unitrack.db`

### Pre-deploy checklist
- [ ] Real `SECRET_KEY` set in platform env vars
- [ ] `.env` removed from git history
- [ ] `gunicorn` added to `requirements.txt`
- [ ] `FLASK_ENV=production` set in platform env vars
- [ ] Database path points to persistent volume
- [ ] Test `python wsgi.py` locally doesn't crash

---

## Git Workflow

After completing any meaningful unit of work — a feature, a fix, a refactor, a structural change — **ask the user whether to commit and push before continuing**. Don't auto-commit. Good checkpoints include:

- Finishing a feature end-to-end (e.g., complete/delete tasks working)
- Fixing a deployment blocker
- A clean structural change like the folder reorganization
- Any time the app is in a working, tested state after a set of changes

Ask like: *"This is a good checkpoint — want me to commit and push?"* then wait for confirmation before running any git commands.

---

## Coding Conventions

- **No new DB logic in routes** — all queries go in `app/database.py` as methods on `Database`
- **Templates extend `base.html`** — flash messages and nav are handled there
- **CSS variables for colors** — all pink values are in `:root` at top of `style.css`; never hardcode hex colors in new CSS
- **Form submissions are POST** — never GET for mutations
- **Route names match function names** — `url_for('dashboard')`, `url_for('calendar_view')` etc.
- **No JavaScript files yet** — inline `<script>` in templates is fine for now; move to `static/js/` when it grows
- **`python-dotenv` loads `.env` automatically** via Flask's dev server — no explicit `load_dotenv()` call needed
