import sqlite3
import threading
from datetime import datetime
from typing import List, Optional, Dict

_UNSET = object()


class Database:
    """SQLite database layer for UniTrack."""

    def __init__(self, db_path: str = "unitrack.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
            self.local.conn.execute("PRAGMA foreign_keys = ON")
        return self.local.conn

    def init_db(self) -> None:
        conn = self.get_connection()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT    NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT    NOT NULL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT    NOT NULL,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                course_id   INTEGER,
                due_date    TEXT,
                status      TEXT    NOT NULL DEFAULT 'Pending',
                created_at  TEXT    NOT NULL,
                description TEXT,
                user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
            )
        """)

        # Migrations for older databases
        for stmt in [
            "ALTER TABLE tasks   ADD COLUMN description TEXT",
            "ALTER TABLE tasks   ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
            "ALTER TABLE courses ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
        ]:
            try:
                c.execute(stmt)
            except sqlite3.OperationalError:
                pass

        conn.commit()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def create_user(self, email: str, password_hash: str) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, password_hash, datetime.now().isoformat()),
        )
        conn.commit()
        return c.lastrowid

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        c = self.get_connection().cursor()
        c.execute("SELECT id, email, password_hash, created_at FROM users WHERE email = ?", (email,))
        return self._user_row(c.fetchone())

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        c = self.get_connection().cursor()
        c.execute("SELECT id, email, password_hash, created_at FROM users WHERE id = ?", (user_id,))
        return self._user_row(c.fetchone())

    @staticmethod
    def _user_row(row) -> Optional[Dict]:
        if not row:
            return None
        return {"id": row["id"], "email": row["email"],
                "password_hash": row["password_hash"], "created_at": row["created_at"]}

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------

    def get_courses(self, user_id: int) -> List[Dict]:
        c = self.get_connection().cursor()
        c.execute("SELECT id, name FROM courses WHERE user_id = ? ORDER BY name", (user_id,))
        return [{"id": r["id"], "name": r["name"]} for r in c.fetchall()]

    def add_course(self, name: str, user_id: int) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM courses WHERE name = ? AND user_id = ?", (name, user_id))
        row = c.fetchone()
        if row:
            return row["id"]
        c.execute("INSERT INTO courses (name, user_id) VALUES (?, ?)", (name, user_id))
        conn.commit()
        return c.lastrowid

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def add_inbox_item(self, title: str, user_id: int) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO tasks (title, course_id, status, created_at, user_id) VALUES (?, ?, ?, ?, ?)",
            (title, None, "Inbox", datetime.now().isoformat(), user_id),
        )
        conn.commit()
        return c.lastrowid

    def get_inbox_items(self, user_id: int) -> List[Dict]:
        c = self.get_connection().cursor()
        c.execute(
            "SELECT id, title, created_at, description FROM tasks "
            "WHERE status = ? AND user_id = ? ORDER BY created_at",
            ("Inbox", user_id),
        )
        return [
            {"id": r["id"], "title": r["title"],
             "created_at": r["created_at"], "description": r["description"] or ""}
            for r in c.fetchall()
        ]

    def update_task_from_inbox(
        self, task_id: int, course_id: Optional[int],
        due_date: Optional[str], description: Optional[str] = None,
        user_id: int = None,
    ) -> None:
        conn = self.get_connection()
        conn.cursor().execute(
            "UPDATE tasks SET course_id=?, due_date=?, description=?, status=? "
            "WHERE id=? AND user_id=?",
            (course_id, due_date, description, "Pending", task_id, user_id),
        )
        conn.commit()

    def get_tasks_by_status(self, status: str, user_id: int) -> List[Dict]:
        c = self.get_connection().cursor()
        c.execute("""
            SELECT t.id, t.title, t.course_id, t.due_date,
                   t.status, t.created_at, t.description, c.name AS course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.status = ? AND t.user_id = ?
            ORDER BY c.name IS NULL, c.name, t.due_date IS NULL, t.due_date
        """, (status, user_id))
        return [self._row_to_dict(r) for r in c.fetchall()]

    def get_tasks_with_due_dates(self, user_id: int) -> List[Dict]:
        c = self.get_connection().cursor()
        c.execute("""
            SELECT t.id, t.title, t.course_id, t.due_date,
                   t.status, t.created_at, t.description, c.name AS course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.due_date IS NOT NULL AND t.due_date != '' AND t.user_id = ?
            ORDER BY t.due_date, t.status
        """, (user_id,))
        return [self._row_to_dict(r) for r in c.fetchall()]

    def get_task_by_id(self, task_id: int, user_id: int) -> Optional[Dict]:
        c = self.get_connection().cursor()
        c.execute("""
            SELECT t.id, t.title, t.course_id, t.due_date,
                   t.status, t.created_at, t.description, c.name AS course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.id = ? AND t.user_id = ?
        """, (task_id, user_id))
        row = c.fetchone()
        return self._row_to_dict(row) if row else None

    def update_task(
        self, task_id: int, user_id: int,
        title=_UNSET, course_id=_UNSET, due_date=_UNSET,
        status=_UNSET, description=_UNSET,
    ) -> None:
        conn = self.get_connection()
        updates, params = [], []

        if title       is not _UNSET: updates.append("title = ?");       params.append(title)
        if course_id   is not _UNSET: updates.append("course_id = ?");   params.append(course_id)
        if due_date    is not _UNSET: updates.append("due_date = ?");     params.append(due_date)
        if status      is not _UNSET: updates.append("status = ?");       params.append(status)
        if description is not _UNSET: updates.append("description = ?");  params.append(description)

        if not updates:
            return

        params += [task_id, user_id]
        conn.cursor().execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ? AND user_id = ?", params
        )
        conn.commit()

    def delete_task(self, task_id: int, user_id: int) -> None:
        conn = self.get_connection()
        conn.cursor().execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        conn.commit()

    def close(self) -> None:
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None

    @staticmethod
    def _row_to_dict(row) -> Dict:
        return {
            "id": row["id"], "title": row["title"],
            "course_id": row["course_id"], "course_name": row["course_name"],
            "due_date": row["due_date"], "status": row["status"],
            "created_at": row["created_at"], "description": row["description"] or "",
        }
