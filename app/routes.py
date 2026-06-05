import re
import socket
import ipaddress
import calendar
import requests as http
from urllib.parse import urlparse
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date


def _annotate_due(task, today, show_urgency=True):
    """Add due_label (human-readable) and due_status (urgency class) to a task dict."""
    raw = task.get("due_date")
    if not raw:
        task["due_label"] = None
        task["due_status"] = None
        return task
    try:
        due = date.fromisoformat(raw)
        task["due_label"] = f"{due.strftime('%b')} {due.day}"
        if not show_urgency:
            task["due_status"] = None
            return task
        delta = (due - today).days
        if delta < 0:
            days = abs(delta)
            task["due_status"] = "overdue"
            task["due_label"] = f"{days} day{'s' if days != 1 else ''} overdue"
        elif delta == 0:
            task["due_status"] = "due-today"
            task["due_label"] = "Due today"
        elif delta <= 2:
            task["due_status"] = "due-soon"
            task["due_label"] = f"Due in {delta} day{'s' if delta != 1 else ''}"
        else:
            task["due_status"] = "future"
    except (ValueError, TypeError):
        task["due_label"] = raw
        task["due_status"] = None
    return task


def register_routes(app, db):

    @app.route('/')
    def landing():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('landing.html')

    _URGENCY_TIERS = [
        ('overdue',   'Overdue'),
        ('due-today', 'Due today'),
        ('due-soon',  'Due in 1-2 days'),
        ('future',    'Coming up'),
        ('none',      'No date'),
    ]

    @app.route('/dashboard')
    @login_required
    def dashboard():
        inbox_items  = db.get_inbox_items(current_user.id)
        today        = date.today()
        tasks        = [_annotate_due(t, today, show_urgency=True)
                        for t in db.get_tasks_by_status("Pending", current_user.id)]
        done_tasks   = [_annotate_due(t, today, show_urgency=False)
                        for t in db.get_tasks_by_status("Done",    current_user.id)]

        view_mode = request.args.get('view', 'course')
        if view_mode not in ('course', 'urgency'):
            view_mode = 'course'

        urgency_tiers, tasks_by_course, unassigned_tasks = [], {}, []

        if view_mode == 'urgency':
            tier_map = {key: [] for key, _ in _URGENCY_TIERS}
            for task in tasks:
                tier_map[task['due_status'] or 'none'].append(task)
            urgency_tiers = [
                {'status': key, 'label': label, 'tasks': tier_map[key]}
                for key, label in _URGENCY_TIERS
                if tier_map[key]
            ]
        else:
            for task in tasks:
                name = task["course_name"] or "Unassigned"
                if name == "Unassigned":
                    unassigned_tasks.append(task)
                else:
                    tasks_by_course.setdefault(name, []).append(task)

        done_by_course, done_unassigned = {}, []
        for task in done_tasks:
            name = task["course_name"] or "Unassigned"
            if name == "Unassigned":
                done_unassigned.append(task)
            else:
                done_by_course.setdefault(name, []).append(task)

        return render_template('dashboard.html',
                               inbox_items=inbox_items,
                               view_mode=view_mode,
                               urgency_tiers=urgency_tiers,
                               tasks_by_course=tasks_by_course,
                               unassigned_tasks=unassigned_tasks,
                               done_by_course=done_by_course,
                               done_unassigned=done_unassigned)

    @app.route('/add-quick-note', methods=['GET', 'POST'])
    @login_required
    def add_quick_note():
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            if not title:
                flash('Task title cannot be empty!', 'error')
                return redirect(url_for('add_quick_note'))
            db.add_inbox_item(title, current_user.id)
            flash('Task added to Inbox!', 'success')
            return redirect(url_for('dashboard'))
        return render_template('tasks/add_quick_note.html')

    @app.route('/process-inbox')
    @login_required
    def process_inbox():
        inbox_items = db.get_inbox_items(current_user.id)
        courses = db.get_courses(current_user.id)
        if not inbox_items:
            flash('No items in Inbox to process.', 'info')
            return redirect(url_for('dashboard'))
        return render_template('tasks/process_inbox.html',
                               inbox_items=inbox_items, courses=courses)

    @app.route('/process-task/<int:task_id>', methods=['POST'])
    @login_required
    def process_task(task_id):
        course_id   = request.form.get('course_id')
        due_date    = request.form.get('due_date', '').strip()
        description = request.form.get('description', '').strip()

        if course_id and course_id.isdigit():
            course_id = int(course_id)
        elif course_id == 'new':
            new_name = request.form.get('new_course_name', '').strip()
            course_id = db.add_course(new_name, current_user.id) if new_name else None
        else:
            course_id = None

        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                flash('Invalid date format. Date skipped.', 'error')
                due_date = None
        else:
            due_date = None

        db.update_task_from_inbox(task_id, course_id, due_date,
                                  description or None, user_id=current_user.id)
        flash('Task processed and moved to Pending!', 'success')
        return redirect(url_for('process_inbox'))

    @app.route('/calendar')
    @login_required
    def calendar_view():
        year  = request.args.get('year',  type=int)
        month = request.args.get('month', type=int)

        if not year or not month:
            today = date.today()
            year, month = today.year, today.month

        month = max(1, min(12, month))
        year  = max(2000, min(2100, year))

        all_tasks    = db.get_tasks_with_due_dates(current_user.id)
        tasks_by_date = {}
        for task in all_tasks:
            try:
                key = datetime.strptime(task["due_date"], "%Y-%m-%d").date().isoformat()
                tasks_by_date.setdefault(key, []).append(task)
            except (ValueError, TypeError):
                continue

        cal        = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]

        month_tasks_by_day = {}
        for week in cal:
            for day in week:
                if day:
                    key = f"{year:04d}-{month:02d}-{day:02d}"
                    month_tasks_by_day[day] = tasks_by_date.get(key, [])

        prev_month, prev_year = month - 1, year
        if prev_month == 0:
            prev_month, prev_year = 12, year - 1

        next_month, next_year = month + 1, year
        if next_month == 13:
            next_month, next_year = 1, year + 1

        return render_template('calendar.html',
                               year=year, month=month, month_name=month_name,
                               calendar=cal, tasks_by_day=month_tasks_by_day,
                               prev_year=prev_year, prev_month=prev_month,
                               next_year=next_year, next_month=next_month,
                               today=date.today())

    @app.route('/add-course', methods=['GET', 'POST'])
    @login_required
    def add_course():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            if not name:
                flash('Course name cannot be empty!', 'error')
                return redirect(url_for('add_course'))
            db.add_course(name, current_user.id)
            flash(f'Course "{name}" added!', 'success')
            return redirect(url_for('dashboard'))
        return render_template('courses/add_course.html')

    @app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
    @login_required
    def edit_task(task_id):
        task = db.get_task_by_id(task_id, current_user.id)
        if not task:
            flash('Task not found!', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            title       = request.form.get('title', '').strip()
            course_id   = request.form.get('course_id', '').strip()
            due_date    = request.form.get('due_date', '').strip()
            description = request.form.get('description', '').strip()

            if not title:
                flash('Task title cannot be empty!', 'error')
                return redirect(url_for('edit_task', task_id=task_id))

            if course_id == 'new':
                new_name = request.form.get('new_course_name', '').strip()
                course_id = db.add_course(new_name, current_user.id) if new_name else None
            elif course_id in ('', 'none'):
                course_id = None
            elif course_id.isdigit():
                course_id = int(course_id)
            else:
                course_id = None

            if due_date:
                try:
                    datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    flash('Invalid date format. Date not updated.', 'error')
                    due_date = None
            else:
                due_date = None

            db.update_task(task_id, current_user.id,
                           title=title, course_id=course_id,
                           due_date=due_date, description=description or None)
            flash('Task updated!', 'success')
            return redirect(url_for('dashboard'))

        courses = db.get_courses(current_user.id)
        return render_template('tasks/edit_task.html', task=task, courses=courses)

    @app.route('/complete-task/<int:task_id>', methods=['POST'])
    @login_required
    def complete_task(task_id):
        task = db.get_task_by_id(task_id, current_user.id)
        if not task:
            flash('Task not found!', 'error')
            return redirect(url_for('dashboard'))
        db.update_task(task_id, current_user.id, status='Done')
        flash(f'"{task["title"]}" marked as done!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/restore-task/<int:task_id>', methods=['POST'])
    @login_required
    def restore_task(task_id):
        task = db.get_task_by_id(task_id, current_user.id)
        if not task:
            flash('Task not found!', 'error')
            return redirect(url_for('dashboard'))
        db.update_task(task_id, current_user.id, status='Pending')
        flash(f'"{task["title"]}" restored to Pending.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/delete-task/<int:task_id>', methods=['POST'])
    @login_required
    def delete_task(task_id):
        task = db.get_task_by_id(task_id, current_user.id)
        if not task:
            flash('Task not found!', 'error')
            return redirect(url_for('dashboard'))
        db.delete_task(task_id, current_user.id)
        flash('Task deleted.', 'success')
        return redirect(url_for('dashboard'))

    def _safe_url(url: str) -> str | None:
        """Return the validated URL or None if it targets a private/reserved address."""
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return None
        host = parsed.hostname or ''
        if not host:
            return None
        try:
            for info in socket.getaddrinfo(host, None):
                ip = ipaddress.ip_address(info[4][0])
                if (ip.is_private or ip.is_loopback or
                        ip.is_link_local or ip.is_reserved or
                        ip.is_multicast or ip.is_unspecified):
                    return None
        except (socket.gaierror, ValueError):
            return None
        return url

    @app.route('/parse-job-link', methods=['POST'])
    @login_required
    def parse_job_link():
        from bs4 import BeautifulSoup
        import logging

        data = request.get_json(silent=True) or {}
        url  = data.get('url', '').strip()
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        if not _safe_url(url):
            return jsonify({'error': 'URL not allowed'}), 400

        try:
            resp = http.get(url, timeout=8, allow_redirects=False, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            # Follow one redirect, re-validating the destination
            if resp.is_redirect:
                dest = resp.headers.get('Location', '')
                if not dest.startswith(('http://', 'https://')):
                    dest = urlparse(url)._replace(path=dest).geturl()
                if not _safe_url(dest):
                    return jsonify({'error': 'URL not allowed'}), 400
                resp = http.get(dest, timeout=8, allow_redirects=False, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
            resp.raise_for_status()

            # Cap response at 2 MB before parsing
            soup = BeautifulSoup(resp.content[:2_097_152], 'html.parser')

            raw_title = soup.title.string.strip() if soup.title else ''
            clean_title = re.sub(
                r'\s*[\|–\-]\s*(LinkedIn|Glassdoor|Indeed|Greenhouse|Lever|Workday|'
                r'Workable|AngelList|Wellfound|ZipRecruiter|Monster|CareerBuilder|Jobs)\b.*$',
                '', raw_title, flags=re.IGNORECASE
            ).strip()

            h1 = soup.find('h1')
            h1_text = h1.get_text(strip=True) if h1 else ''

            meta = (soup.find('meta', attrs={'name': 'description'}) or
                    soup.find('meta', attrs={'property': 'og:description'}))
            description = meta.get('content', '').strip()[:400] if meta else ''

            best = h1_text if (h1_text and len(h1_text) < 80) else clean_title
            suggested_title = f"Apply — {best}" if best else ''

            return jsonify({'suggested_title': suggested_title, 'description': description})

        except Exception:
            logging.exception("parse_job_link failed for url=%s", url)
            return jsonify({'error': 'Could not fetch or parse the URL'}), 422
