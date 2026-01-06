"""
Flask app for UniTrack.
Just a simple local web app with a pink theme.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import Database
from datetime import datetime, date
import sqlite3
import calendar
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-local-use-only')
db = Database()


@app.teardown_appcontext
def close_db(error):
    """Clean up the database connection when the request is done."""
    db.close()


@app.route('/')
def dashboard():
    """Main dashboard showing tasks organized by course."""
    inbox_items = db.get_inbox_items()
    tasks = db.get_tasks_by_status("Pending")
    
    # Organize tasks by course
    tasks_by_course = {}
    unassigned_tasks = []
    
    for task in tasks:
        course_name = task["course_name"] or "Unassigned"
        if course_name == "Unassigned":
            unassigned_tasks.append(task)
        else:
            if course_name not in tasks_by_course:
                tasks_by_course[course_name] = []
            tasks_by_course[course_name].append(task)
    
    return render_template('dashboard.html', 
                         inbox_items=inbox_items,
                         tasks_by_course=tasks_by_course,
                         unassigned_tasks=unassigned_tasks)


@app.route('/add-quick-note', methods=['GET', 'POST'])
def add_quick_note():
    """Quick way to dump a task into the inbox without thinking about details."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Task title cannot be empty!', 'error')
            return redirect(url_for('add_quick_note'))
        
        task_id = db.add_inbox_item(title)
        flash(f'Task added to Inbox (ID: {task_id})', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_quick_note.html')


@app.route('/process-inbox')
def process_inbox():
    """Show all the inbox items so you can assign them to courses."""
    inbox_items = db.get_inbox_items()
    courses = db.get_courses()
    
    if not inbox_items:
        flash('No items in Inbox to process.', 'info')
        return redirect(url_for('dashboard'))
    
    return render_template('process_inbox.html', 
                         inbox_items=inbox_items,
                         courses=courses)


@app.route('/process-task/<int:task_id>', methods=['POST'])
def process_task(task_id):
    """Take an inbox item and assign it to a course, set due date, etc."""
    course_id = request.form.get('course_id')
    due_date = request.form.get('due_date', '').strip()
    description = request.form.get('description', '').strip()
    
    # Figure out what course this should be
    if course_id and course_id.isdigit():
        course_id = int(course_id)
    elif course_id == 'new':
        # User wants to create a new course
        new_course_name = request.form.get('new_course_name', '').strip()
        if new_course_name:
            try:
                course_id = db.add_course(new_course_name)
            except sqlite3.IntegrityError:
                flash(f'Course "{new_course_name}" already exists', 'error')
                return redirect(url_for('process_inbox'))
        else:
            course_id = None
    else:
        course_id = None
    
    # Make sure the date is valid if they provided one
    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            flash('Invalid date format. Date skipped.', 'error')
            due_date = None
    else:
        due_date = None
    
    # Description is optional
    if not description:
        description = None
    
    db.update_task_from_inbox(task_id, course_id, due_date, description)
    flash('Task processed and moved to Pending', 'success')
    return redirect(url_for('process_inbox'))


@app.route('/calendar')
def calendar_view():
    """Show a calendar view of all tasks with due dates."""
    # Get the month/year from URL params, or use current month
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        today = date.today()
        year = today.year
        month = today.month
    
    # Make sure the month/year make sense
    if month < 1 or month > 12:
        month = date.today().month
    if year < 2000 or year > 2100:
        year = date.today().year
    
    # Grab all tasks that have due dates
    all_tasks = db.get_tasks_with_due_dates()
    
    # Put tasks into a dict keyed by their due date
    tasks_by_date = {}
    for task in all_tasks:
        try:
            task_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
            date_key = task_date.isoformat()
            if date_key not in tasks_by_date:
                tasks_by_date[date_key] = []
            tasks_by_date[date_key].append(task)
        except (ValueError, TypeError):
            continue  # Bad date format, just skip it
    
    # Generate the calendar grid
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Map day numbers to tasks for this month
    month_tasks_by_day = {}
    for week in cal:
        for day in week:
            if day != 0:
                date_key = f"{year:04d}-{month:02d}-{day:02d}"
                month_tasks_by_day[day] = tasks_by_date.get(date_key, [])
    
    # Calculate prev/next month for navigation
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1
    
    return render_template('calendar.html',
                         year=year,
                         month=month,
                         month_name=month_name,
                         calendar=cal,
                         tasks_by_day=month_tasks_by_day,
                         prev_year=prev_year,
                         prev_month=prev_month,
                         next_year=next_year,
                         next_month=next_month,
                         today=date.today())


@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    """Create a new course/context."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Course name cannot be empty!', 'error')
            return redirect(url_for('add_course'))
        
        try:
            course_id = db.add_course(name)
            flash(f'Course added (ID: {course_id})', 'success')
        except sqlite3.IntegrityError:
            flash(f'Course "{name}" already exists', 'error')
        
        return redirect(url_for('dashboard'))
    
    return render_template('add_course.html')


@app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    """Edit a task - fix typos, change course, update dates, etc."""
    task = db.get_task_by_id(task_id)
    
    if not task:
        flash('Task not found!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        course_id = request.form.get('course_id', '').strip()
        due_date = request.form.get('due_date', '').strip()
        description = request.form.get('description', '').strip()
        
        # Title is required
        if not title:
            flash('Task title cannot be empty!', 'error')
            return redirect(url_for('edit_task', task_id=task_id))
        
        # Figure out the course
        if course_id == 'new':
            # They want to create a new course
            new_course_name = request.form.get('new_course_name', '').strip()
            if new_course_name:
                try:
                    course_id = db.add_course(new_course_name)
                except sqlite3.IntegrityError:
                    flash(f'Course "{new_course_name}" already exists', 'error')
                    return redirect(url_for('edit_task', task_id=task_id))
            else:
                course_id = None
        elif course_id == '' or course_id == 'none':
            course_id = None
        elif course_id.isdigit():
            course_id = int(course_id)
        else:
            course_id = None
        
        # Check the date format
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                flash('Invalid date format. Date not updated.', 'error')
                due_date = None
        else:
            due_date = None
        
        # Description is optional
        if not description:
            description = None
        
        # Save the changes
        db.update_task(
            task_id=task_id,
            title=title,
            course_id=course_id,
            due_date=due_date,
            description=description
        )
        
        flash('Task updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Show the edit form
    courses = db.get_courses()
    return render_template('edit_task.html', task=task, courses=courses)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
