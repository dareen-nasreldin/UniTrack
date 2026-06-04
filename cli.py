"""
UniTrack CLI — terminal interface using rich.
Run with: python cli.py
"""

import sys
import sqlite3
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from app.database import Database


class UniTrackCLI:
    """Terminal interface for UniTrack."""

    def __init__(self):
        self.db = Database()
        self.console = Console()

    def show_dashboard(self) -> None:
        inbox_items = self.db.get_inbox_items()

        if inbox_items:
            self.console.print(Panel(
                f"[bold yellow]⚠️  You have {len(inbox_items)} item(s) in your Inbox![/bold yellow]",
                style="yellow", border_style="yellow"
            ))
            self.console.print()

        tasks = self.db.get_tasks_by_status("Pending")

        if not tasks and not inbox_items:
            self.console.print("[dim]No tasks found. Add a task to get started![/dim]")
            return

        tasks_by_course: dict = {}
        unassigned_tasks = []

        for task in tasks:
            course_name = task["course_name"] or "Unassigned"
            if course_name == "Unassigned":
                unassigned_tasks.append(task)
            else:
                tasks_by_course.setdefault(course_name, []).append(task)

        table = Table(title="📚 UniTrack Dashboard", show_header=True, header_style="bold magenta")
        table.add_column("Course", style="cyan", width=20)
        table.add_column("Task", style="white", width=40)
        table.add_column("Due Date", style="yellow", width=15)

        for task in unassigned_tasks:
            table.add_row("[dim]Unassigned[/dim]", task["title"], task["due_date"] or "[dim]No date[/dim]")

        for course_name in sorted(tasks_by_course.keys()):
            for i, task in enumerate(tasks_by_course[course_name]):
                table.add_row(
                    course_name if i == 0 else "",
                    task["title"],
                    task["due_date"] or "[dim]No date[/dim]",
                )

        self.console.print(table)

    def add_quick_note(self) -> None:
        self.console.print("\n[bold cyan]📝 Quick Note (Inbox)[/bold cyan]")
        title = Prompt.ask("Enter task title")

        if not title.strip():
            self.console.print("[red]Task title cannot be empty![/red]")
            return

        task_id = self.db.add_inbox_item(title.strip())
        self.console.print(f"[green]✓ Task added to Inbox (ID: {task_id})[/green]")

    def process_inbox(self) -> None:
        inbox_items = self.db.get_inbox_items()

        if not inbox_items:
            self.console.print("[dim]No items in Inbox to process.[/dim]")
            return

        self.console.print(f"\n[bold cyan]📥 Processing {len(inbox_items)} Inbox item(s)[/bold cyan]\n")
        courses = self.db.get_courses()

        for item in inbox_items:
            self.console.print(f"\n[bold]Task:[/bold] {item['title']}")
            self.console.print(f"[dim]Created: {item['created_at']}[/dim]")

            if courses:
                self.console.print("\n[cyan]Available Courses:[/cyan]")
                for idx, course in enumerate(courses, 1):
                    self.console.print(f"  {idx}. {course['name']}")

            course_choice = Prompt.ask(
                "\nSelect course number (or Enter to skip, 'new' to create)",
                default=""
            )

            course_id = None
            if course_choice.lower() == "new":
                course_name = Prompt.ask("Enter new course name")
                if course_name.strip():
                    course_id = self.db.add_course(course_name.strip())
                    courses = self.db.get_courses()
                    self.console.print(f"[green]✓ Course '{course_name}' created[/green]")
            elif course_choice.isdigit():
                idx = int(course_choice)
                if 1 <= idx <= len(courses):
                    course_id = courses[idx - 1]["id"]

            due_date = Prompt.ask("Enter due date (YYYY-MM-DD or Enter to skip)", default="")

            if due_date.strip():
                try:
                    datetime.strptime(due_date.strip(), "%Y-%m-%d")
                    due_date = due_date.strip()
                except ValueError:
                    self.console.print("[yellow]⚠ Invalid date format. Skipping date.[/yellow]")
                    due_date = None
            else:
                due_date = None

            self.db.update_task_from_inbox(item["id"], course_id, due_date)
            self.console.print("[green]✓ Task processed and moved to Pending[/green]")

    def add_course(self) -> None:
        self.console.print("\n[bold cyan]➕ Add Course[/bold cyan]")
        name = Prompt.ask("Enter course name")

        if not name.strip():
            self.console.print("[red]Course name cannot be empty![/red]")
            return

        try:
            course_id = self.db.add_course(name.strip())
            self.console.print(f"[green]✓ Course added (ID: {course_id})[/green]")
        except sqlite3.IntegrityError:
            self.console.print(f"[yellow]⚠ Course '{name}' already exists[/yellow]")

    def show_menu(self) -> None:
        menu = Table.grid(padding=(0, 2))
        menu.add_row("[bold cyan]1.[/bold cyan]", "View Dashboard")
        menu.add_row("[bold cyan]2.[/bold cyan]", "Add Quick Note (Inbox)")
        menu.add_row("[bold cyan]3.[/bold cyan]", "Process Inbox")
        menu.add_row("[bold cyan]4.[/bold cyan]", "Add Course")
        menu.add_row("[bold cyan]5.[/bold cyan]", "Exit")
        self.console.print("\n[bold magenta]📚 UniTrack CLI[/bold magenta]")
        self.console.print(menu)

    def run(self) -> None:
        try:
            while True:
                self.show_menu()
                choice = Prompt.ask("\n[cyan]Select an option[/cyan]", choices=["1", "2", "3", "4", "5"], default="1")

                if choice == "1":
                    self.console.print()
                    self.show_dashboard()
                elif choice == "2":
                    self.add_quick_note()
                elif choice == "3":
                    self.process_inbox()
                elif choice == "4":
                    self.add_course()
                elif choice == "5":
                    self.console.print("\n[green]Goodbye! 👋[/green]")
                    break

                if choice != "5":
                    Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
                    self.console.print()

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Interrupted. Goodbye! 👋[/yellow]")
        finally:
            self.db.close()


if __name__ == "__main__":
    cli = UniTrackCLI()
    cli.run()
