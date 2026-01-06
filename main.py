"""
Main CLI module for UniTrack.
Handles CLI logic and UI using rich library.
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
from database import Database


class UniTrackCLI:
    """Main CLI interface for UniTrack."""
    
    def __init__(self):
        """Initialize CLI with database connection."""
        self.db = Database()
        self.console = Console()
    
    def show_dashboard(self) -> None:
        """Display grouped dashboard with tasks organized by course."""
        # Get inbox items
        inbox_items = self.db.get_inbox_items()
        
        # Show inbox alert if there are items
        if inbox_items:
            inbox_text = f"[bold yellow]⚠️  You have {len(inbox_items)} item(s) in your Inbox![/bold yellow]"
            self.console.print(Panel(inbox_text, style="yellow", border_style="yellow"))
            self.console.print()
        
        # Get pending tasks
        tasks = self.db.get_tasks_by_status("Pending")
        
        if not tasks and not inbox_items:
            self.console.print("[dim]No tasks found. Add a task to get started![/dim]")
            return
        
        # Group tasks by course
        tasks_by_course: dict = {}
        unassigned_tasks = []
        
        for task in tasks:
            course_name = task["course_name"] or "Unassigned"
            if course_name == "Unassigned":
                unassigned_tasks.append(task)
            else:
                if course_name not in tasks_by_course:
                    tasks_by_course[course_name] = []
                tasks_by_course[course_name].append(task)
        
        # Create and display table
        table = Table(title="📚 UniTrack Dashboard - Pending Tasks", show_header=True, header_style="bold magenta")
        table.add_column("Course", style="cyan", width=20)
        table.add_column("Task", style="white", width=40)
        table.add_column("Due Date", style="yellow", width=15)
        table.add_column("ID", style="dim", width=5)
        
        # Add unassigned tasks first
        if unassigned_tasks:
            for task in unassigned_tasks:
                due_date = task["due_date"] or "[dim]No date[/dim]"
                table.add_row(
                    "[dim]Unassigned[/dim]",
                    task["title"],
                    due_date,
                    str(task["id"])
                )
        
        # Add tasks grouped by course
        for course_name in sorted(tasks_by_course.keys()):
            course_tasks = tasks_by_course[course_name]
            for i, task in enumerate(course_tasks):
                due_date = task["due_date"] or "[dim]No date[/dim]"
                # Show course name only for first task in group
                course_display = course_name if i == 0 else ""
                table.add_row(
                    course_display,
                    task["title"],
                    due_date,
                    str(task["id"])
                )
        
        self.console.print(table)
    
    def add_quick_note(self) -> None:
        """Add a quick note to the Inbox."""
        self.console.print("\n[bold cyan]📝 Quick Note (Inbox)[/bold cyan]")
        title = Prompt.ask("Enter task title")
        
        if not title.strip():
            self.console.print("[red]Task title cannot be empty![/red]")
            return
        
        task_id = self.db.add_inbox_item(title.strip())
        self.console.print(f"[green]✓ Task added to Inbox (ID: {task_id})[/green]")
    
    def process_inbox(self) -> None:
        """Process Inbox items by assigning them to courses and dates."""
        inbox_items = self.db.get_inbox_items()
        
        if not inbox_items:
            self.console.print("[dim]No items in Inbox to process.[/dim]")
            return
        
        self.console.print(f"\n[bold cyan]📥 Processing {len(inbox_items)} Inbox item(s)[/bold cyan]\n")
        
        courses = self.db.get_courses()
        course_map = {str(i + 1): course for i, course in enumerate(courses)}
        
        for item in inbox_items:
            self.console.print(f"\n[bold]Task:[/bold] {item['title']}")
            self.console.print(f"[dim]Created: {item['created_at']}[/dim]")
            
            # Show available courses
            if courses:
                self.console.print("\n[cyan]Available Courses:[/cyan]")
                for idx, course in enumerate(courses, 1):
                    self.console.print(f"  {idx}. {course['name']}")
            
            # Prompt for course selection
            if courses:
                course_choice = Prompt.ask(
                    "\nSelect course number (or press Enter to skip, 'new' to create new course)",
                    default=""
                )
            else:
                course_choice = Prompt.ask(
                    "\nEnter course name (or press Enter to skip)",
                    default=""
                )
            
            course_id = None
            
            if course_choice.lower() == "new" or (not courses and course_choice.strip()):
                # Create new course
                course_name = Prompt.ask("Enter new course name")
                if course_name.strip():
                    course_id = self.db.add_course(course_name.strip())
                    courses = self.db.get_courses()  # Refresh list
                    course_map = {str(i + 1): course for i, course in enumerate(courses)}
                    self.console.print(f"[green]✓ Course '{course_name}' created[/green]")
            elif course_choice.strip() and course_choice in course_map:
                course_id = course_map[course_choice]["id"]
            elif course_choice.strip() and course_choice.isdigit():
                idx = int(course_choice)
                if 1 <= idx <= len(courses):
                    course_id = courses[idx - 1]["id"]
            
            # Prompt for due date
            due_date = Prompt.ask(
                "Enter due date (YYYY-MM-DD or press Enter to skip)",
                default=""
            )
            
            # Validate date format if provided
            if due_date.strip():
                try:
                    datetime.strptime(due_date.strip(), "%Y-%m-%d")
                    due_date = due_date.strip()
                except ValueError:
                    self.console.print("[yellow]⚠ Invalid date format. Skipping date.[/yellow]")
                    due_date = None
            else:
                due_date = None
            
            # Update task
            self.db.update_task_from_inbox(item["id"], course_id, due_date)
            self.console.print(f"[green]✓ Task processed and moved to Pending[/green]")
    
    def add_course(self) -> None:
        """Add a new course."""
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
        """Display main menu."""
        menu = Table.grid(padding=(0, 2))
        menu.add_row("[bold cyan]1.[/bold cyan]", "View Dashboard")
        menu.add_row("[bold cyan]2.[/bold cyan]", "Add Quick Note (Inbox)")
        menu.add_row("[bold cyan]3.[/bold cyan]", "Process Inbox")
        menu.add_row("[bold cyan]4.[/bold cyan]", "Add Course")
        menu.add_row("[bold cyan]5.[/bold cyan]", "Exit")
        
        self.console.print("\n[bold magenta]📚 UniTrack CLI[/bold magenta]")
        self.console.print(menu)
    
    def run(self) -> None:
        """Main CLI loop."""
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
