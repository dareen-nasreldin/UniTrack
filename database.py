"""
Database stuff for UniTrack.
Just handles all the SQLite database operations.
Made thread-safe so Flask doesn't break things.
"""

import sqlite3
import threading
from datetime import datetime
from typing import List, Optional, Tuple, Dict


class Database:
    """Takes care of all database operations."""
    
    def __init__(self, db_path: str = "unitrack.db"):
        """Set up the database connection."""
        self.db_path = db_path
        self.local = threading.local()  # Each thread gets its own connection
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """Grab a connection for this thread, create one if needed."""
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False  # Flask uses multiple threads, so we need this
            )
            self.local.conn.row_factory = sqlite3.Row  # Makes it easier to access columns by name
            # Turn on foreign keys so relationships work properly
            self.local.conn.execute("PRAGMA foreign_keys = ON")
        return self.local.conn
    
    def init_db(self) -> None:
        """Set up the database tables if they don't exist yet."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Courses table - just stores course names
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        
        # Tasks table - the main one
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
        
        # Add description column if it's missing (for old databases)
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN description TEXT")
        except sqlite3.OperationalError:
            pass  # Already there, no big deal
        
        conn.commit()
    
    def get_courses(self) -> List[Dict]:
        """Get all the courses, sorted by name."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM courses ORDER BY name")
        rows = cursor.fetchall()
        return [{"id": row["id"], "name": row["name"]} for row in rows]
    
    def add_course(self, name: str) -> int:
        """
        Add a course, or return the ID if it already exists.
        Returns the course ID either way.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # See if we already have this course
        cursor.execute("SELECT id FROM courses WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            return row["id"]
        
        # Nope, create a new one
        cursor.execute("INSERT INTO courses (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid
    
    def add_inbox_item(self, title: str) -> int:
        """
        Quick way to add a task to the inbox.
        Just needs a title, everything else is set to defaults.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO tasks (title, course_id, status, created_at) VALUES (?, ?, ?, ?)",
            (title, None, "Inbox", created_at)
        )
        conn.commit()
        return cursor.lastrowid
    
    def get_inbox_items(self) -> List[Dict]:
        """Get all the inbox items, ordered by when they were created."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, created_at, description FROM tasks WHERE status = ? ORDER BY created_at",
            ("Inbox",)
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"], 
                "title": row["title"], 
                "created_at": row["created_at"],
                "description": row["description"] if row["description"] else ""
            }
            for row in rows
        ]
    
    def update_task_from_inbox(
        self, task_id: int, course_id: Optional[int], due_date: Optional[str], description: Optional[str] = None
    ) -> None:
        """
        When processing an inbox item, assign it to a course and set the due date.
        Also moves it from Inbox to Pending status.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET course_id = ?, due_date = ?, description = ?, status = ? WHERE id = ?",
            (course_id, due_date, description, "Pending", task_id)
        )
        conn.commit()
    
    def get_tasks_by_status(self, status: str = "Pending") -> List[Dict]:
        """
        Get all tasks with a specific status, including their course info.
        Uses a JOIN so we get the course name too.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.id,
                t.title,
                t.course_id,
                t.due_date,
                t.status,
                t.created_at,
                t.description,
                c.name as course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.status = ?
            ORDER BY c.name IS NULL, c.name, t.due_date IS NULL, t.due_date
        """, (status,))
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "course_id": row["course_id"],
                "course_name": row["course_name"],
                "due_date": row["due_date"],
                "status": row["status"],
                "created_at": row["created_at"],
                "description": row["description"] if row["description"] else ""
            }
            for row in rows
        ]
    
    def get_tasks_with_due_dates(self) -> List[Dict]:
        """
        Get all tasks that have a due date, no matter what status they're in.
        Used for the calendar view.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.id,
                t.title,
                t.course_id,
                t.due_date,
                t.status,
                t.created_at,
                t.description,
                c.name as course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.due_date IS NOT NULL AND t.due_date != ''
            ORDER BY t.due_date, t.status
        """)
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "course_id": row["course_id"],
                "course_name": row["course_name"],
                "due_date": row["due_date"],
                "status": row["status"],
                "created_at": row["created_at"],
                "description": row["description"] if row["description"] else ""
            }
            for row in rows
        ]
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Grab a specific task by its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.id,
                t.title,
                t.course_id,
                t.due_date,
                t.status,
                t.created_at,
                t.description,
                c.name as course_name
            FROM tasks t
            LEFT JOIN courses c ON t.course_id = c.id
            WHERE t.id = ?
        """, (task_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "title": row["title"],
                "course_id": row["course_id"],
                "course_name": row["course_name"],
                "due_date": row["due_date"],
                "status": row["status"],
                "created_at": row["created_at"],
                "description": row["description"] if row["description"] else ""
            }
        return None
    
    def update_task(
        self, 
        task_id: int, 
        title: Optional[str] = None,
        course_id: Optional[int] = None,
        due_date: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Update whatever fields you pass in. Only updates the ones that aren't None.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build the UPDATE query dynamically based on what's being changed
        updates = []
        params = []
        
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
            return  # Nothing to do here
        
        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    def close(self) -> None:
        """Clean up the connection for this thread."""
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None
