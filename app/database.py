import threading
from typing import List, Optional, Dict

import psycopg2
import psycopg2.extras

_UNSET = object()


class Database:
    """PostgreSQL database layer for UniTrack (via Supabase)."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.local = threading.local()

    def get_connection(self):
        conn = getattr(self.local, 'conn', None)
        if conn is None or conn.closed:
            self.local.conn = psycopg2.connect(
                self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
                sslmode='require',
            )
        return self.local.conn

    def init_db(self) -> None:
        # Schema is managed via Supabase migrations — nothing to do here.
        pass

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def create_user(self, email: str, password_hash: str) -> int:
        conn = self.get_connection()
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, password_hash),
            )
            user_id = c.fetchone()["id"]
        conn.commit()
        return user_id

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        with self.get_connection().cursor() as c:
            c.execute(
                "SELECT id, email, password_hash, created_at FROM users WHERE email = %s",
                (email,),
            )
            return self._user_row(c.fetchone())

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        with self.get_connection().cursor() as c:
            c.execute(
                "SELECT id, email, password_hash, created_at FROM users WHERE id = %s",
                (user_id,),
            )
            return self._user_row(c.fetchone())

    @staticmethod
    def _user_row(row) -> Optional[Dict]:
        if not row:
            return None
        return {
            "id": row["id"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else "",
        }

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------

    def get_courses(self, user_id: int) -> List[Dict]:
        with self.get_connection().cursor() as c:
            c.execute(
                "SELECT id, name FROM courses WHERE user_id = %s ORDER BY name",
                (user_id,),
            )
            return [{"id": r["id"], "name": r["name"]} for r in c.fetchall()]

    def add_course(self, name: str, user_id: int) -> int:
        conn = self.get_connection()
        with conn.cursor() as c:
            c.execute(
                "SELECT id FROM courses WHERE name = %s AND user_id = %s",
                (name, user_id),
            )
            row = c.fetchone()
            if row:
                return row["id"]
            c.execute(
                "INSERT INTO courses (name, user_id) VALUES (%s, %s) RETURNING id",
                (name, user_id),
            )
            course_id = c.fetchone()["id"]
        conn.commit()
        return course_id

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def add_inbox_item(self, title: str, user_id: int) -> int:
        conn = self.get_connection()
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO tasks (title, status, user_id) VALUES (%s, %s, %s) RETURNING id",
                (title, "Inbox", user_id),
            )
            task_id = c.fetchone()["id"]
        conn.commit()
        return task_id

    def get_inbox_items(self, user_id: int) -> List[Dict]:
        with self.get_connection().cursor() as c:
            c.execute(
                "SELECT id, title, created_at, description FROM tasks "
                "WHERE status = %s AND user_id = %s ORDER BY created_at",
                ("Inbox", user_id),
            )
            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else "",
                    "description": r["description"] or "",
                }
                for r in c.fetchall()
            ]

    def update_task_from_inbox(
        self,
        task_id: int,
        course_id: Optional[int],
        due_date: Optional[str],
        description: Optional[str] = None,
        user_id: int = None,
    ) -> None:
        conn = self.get_connection()
        with conn.cursor() as c:
            c.execute(
                "UPDATE tasks SET course_id=%s, due_date=%s, description=%s, status=%s "
                "WHERE id=%s AND user_id=%s",
                (course_id, due_date, description, "Pending", task_id, user_id),
            )
        conn.commit()

    def get_tasks_by_status(self, status: str, user_id: int) -> List[Dict]:
        with self.get_connection().cursor() as c:
            c.execute(
                """
                SELECT t.id, t.title, t.course_id, t.due_date,
                       t.status, t.created_at, t.description, c.name AS course_name
                FROM tasks t
                LEFT JOIN courses c ON t.course_id = c.id
                WHERE t.status = %s AND t.user_id = %s
                ORDER BY c.name IS NULL, c.name, t.due_date IS NULL, t.due_date
                """,
                (status, user_id),
            )
            return [self._row_to_dict(r) for r in c.fetchall()]

    def get_tasks_with_due_dates(self, user_id: int) -> List[Dict]:
        with self.get_connection().cursor() as c:
            c.execute(
                """
                SELECT t.id, t.title, t.course_id, t.due_date,
                       t.status, t.created_at, t.description, c.name AS course_name
                FROM tasks t
                LEFT JOIN courses c ON t.course_id = c.id
                WHERE t.due_date IS NOT NULL AND t.user_id = %s
                ORDER BY t.due_date, t.status
                """,
                (user_id,),
            )
            return [self._row_to_dict(r) for r in c.fetchall()]

    def get_task_by_id(self, task_id: int, user_id: int) -> Optional[Dict]:
        with self.get_connection().cursor() as c:
            c.execute(
                """
                SELECT t.id, t.title, t.course_id, t.due_date,
                       t.status, t.created_at, t.description, c.name AS course_name
                FROM tasks t
                LEFT JOIN courses c ON t.course_id = c.id
                WHERE t.id = %s AND t.user_id = %s
                """,
                (task_id, user_id),
            )
            row = c.fetchone()
        return self._row_to_dict(row) if row else None

    def update_task(
        self,
        task_id: int,
        user_id: int,
        title=_UNSET,
        course_id=_UNSET,
        due_date=_UNSET,
        status=_UNSET,
        description=_UNSET,
    ) -> None:
        conn = self.get_connection()
        updates, params = [], []

        if title       is not _UNSET: updates.append("title = %s");       params.append(title)
        if course_id   is not _UNSET: updates.append("course_id = %s");   params.append(course_id)
        if due_date    is not _UNSET: updates.append("due_date = %s");     params.append(due_date)
        if status      is not _UNSET: updates.append("status = %s");       params.append(status)
        if description is not _UNSET: updates.append("description = %s");  params.append(description)

        if not updates:
            return

        params += [task_id, user_id]
        with conn.cursor() as c:
            c.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s AND user_id = %s",
                params,
            )
        conn.commit()

    def delete_task(self, task_id: int, user_id: int) -> None:
        conn = self.get_connection()
        with conn.cursor() as c:
            c.execute(
                "DELETE FROM tasks WHERE id = %s AND user_id = %s",
                (task_id, user_id),
            )
        conn.commit()

    def close(self) -> None:
        conn = getattr(self.local, 'conn', None)
        if conn and not conn.closed:
            conn.close()
            self.local.conn = None

    @staticmethod
    def _row_to_dict(row) -> Dict:
        due     = row["due_date"]
        created = row["created_at"]
        return {
            "id":          row["id"],
            "title":       row["title"],
            "course_id":   row["course_id"],
            "course_name": row["course_name"],
            "due_date":    due.isoformat() if due else None,
            "status":      row["status"],
            "created_at":  created.isoformat() if created else "",
            "description": row["description"] or "",
        }
