import sqlite3
import threading
from datetime import datetime
from typing import List, Optional, Dict


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
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course_id INTEGER,
                due_date TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
            )
        """)

        # Migrate older databases that lack the description column
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN description TEXT")
        except sqlite3.OperationalError:
            pass

        conn.commit()

    def get_courses(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM courses ORDER BY name")
        return [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]

    def add_course(self, name: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM courses WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row["id"]
        cursor.execute("INSERT INTO courses (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid

    def add_inbox_item(self, title: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, course_id, status, created_at) VALUES (?, ?, ?, ?)",
            (title, None, "Inbox", datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid

    def get_inbox_items(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, created_at, description FROM tasks WHERE status = ? ORDER BY created_at",
            ("Inbox",),
        )
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "description": row["description"] or "",
            }
            for row in cursor.fetchall()
        ]

    def update_task_from_inbox(
        self,
        task_id: int,
        course_id: Optional[int],
        due_date: Optional[str],
        description: Optional[str] = None,
    ) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET course_id = ?, due_date = ?, description = ?, status = ? WHERE id = ?",
            (course_id, due_date, description, "Pending", task_id),
        )
        conn.commit()

    def get_tasks_by_status(self, status: str = "Pending") -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                t.id, t.title, t.course_id, t.due_date,
                t.status, t.created_at, t.description,
                c.name as course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.status = ?
            ORDER BY c.name IS NULL, c.name, t.due_date IS NULL, t.due_date
        """, (status,))
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_tasks_with_due_dates(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                t.id, t.title, t.course_id, t.due_date,
                t.status, t.created_at, t.description,
                c.name as course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.due_date IS NOT NULL AND t.due_date != ''
            ORDER BY t.due_date, t.status
        """)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                t.id, t.title, t.course_id, t.due_date,
                t.status, t.created_at, t.description,
                c.name as course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.id = ?
        """, (task_id,))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        course_id: Optional[int] = None,
        due_date: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        updates, params = [], []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if course_id is not None:
            updates.append("course_id = ?")
            params.append(course_id)
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return

        params.append(task_id)
        cursor.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    def close(self) -> None:
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None

    @staticmethod
    def _row_to_dict(row) -> Dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "course_id": row["course_id"],
            "course_name": row["course_name"],
            "due_date": row["due_date"],
            "status": row["status"],
            "created_at": row["created_at"],
            "description": row["description"] or "",
        }
