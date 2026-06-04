import sqlite3
import calendar
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime, date


def register_routes(app, db):

    @app.route('/')
    def dashboard():
        inbox_items = db.get_inbox_items()
        tasks = db.get_tasks_by_status("Pending")

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
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            if not title:
                flash('Task title cannot be empty!', 'error')
                return redirect(url_for('add_quick_note'))

            db.add_inbox_item(title)
            flash('Task added to Inbox!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('tasks/add_quick_note.html')

    @app.route('/process-inbox')
    def process_inbox():
        inbox_items = db.get_inbox_items()
        courses = db.get_courses()

        if not inbox_items:
            flash('No items in Inbox to process.', 'info')
            return redirect(url_for('dashboard'))

        return render_template('tasks/process_inbox.html',
                               inbox_items=inbox_items,
                               courses=courses)

    @app.route('/process-task/<int:task_id>', methods=['POST'])
    def process_task(task_id):
        course_id = request.form.get('course_id')
        due_date = request.form.get('due_date', '').strip()
        description = request.form.get('description', '').strip()

        if course_id and course_id.isdigit():
            course_id = int(course_id)
        elif course_id == 'new':
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

        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                flash('Invalid date format. Date skipped.', 'error')
                due_date = None
        else:
            due_date = None

        db.update_task_from_inbox(task_id, course_id, due_date, description or None)
        flash('Task processed and moved to Pending!', 'success')
        return redirect(url_for('process_inbox'))

    @app.route('/calendar')
    def calendar_view():
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month

        if month < 1 or month > 12:
            month = date.today().month
        if year < 2000 or year > 2100:
            year = date.today().year

        all_tasks = db.get_tasks_with_due_dates()

        tasks_by_date = {}
        for task in all_tasks:
            try:
                task_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                date_key = task_date.isoformat()
                if date_key not in tasks_by_date:
                    tasks_by_date[date_key] = []
                tasks_by_date[date_key].append(task)
            except (ValueError, TypeError):
                continue

        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]

        month_tasks_by_day = {}
        for week in cal:
            for day in week:
                if day != 0:
                    date_key = f"{year:04d}-{month:02d}-{day:02d}"
                    month_tasks_by_day[day] = tasks_by_date.get(date_key, [])

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
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            if not name:
                flash('Course name cannot be empty!', 'error')
                return redirect(url_for('add_course'))

            try:
                db.add_course(name)
                flash(f'Course "{name}" added!', 'success')
            except sqlite3.IntegrityError:
                flash(f'Course "{name}" already exists', 'error')

            return redirect(url_for('dashboard'))

        return render_template('courses/add_course.html')

    @app.route('/complete-task/<int:task_id>', methods=['POST'])
    def complete_task(task_id):
        task = db.get_task_by_id(task_id)
        if not task:
            flash('Task not found!', 'error')
            return redirect(url_for('dashboard'))
        db.update_task(task_id=task_id, status='Done')
        flash(f'"{task["title"]}" marked as done!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/delete-task/<int:task_id>', methods=['POST'])
    def delete_task(task_id):
        task = db.get_task_by_id(task_id)
        if not task:
            flash('Task not found!', 'error')
            return redirect(url_for('dashboard'))
        db.delete_task(task_id)
        flash('Task deleted.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
    def edit_task(task_id):
        task = db.get_task_by_id(task_id)

        if not task:
            flash('Task not found!', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            course_id = request.form.get('course_id', '').strip()
            due_date = request.form.get('due_date', '').strip()
            description = request.form.get('description', '').strip()

            if not title:
                flash('Task title cannot be empty!', 'error')
                return redirect(url_for('edit_task', task_id=task_id))

            if course_id == 'new':
                new_course_name = request.form.get('new_course_name', '').strip()
                if new_course_name:
                    try:
                        course_id = db.add_course(new_course_name)
                    except sqlite3.IntegrityError:
                        flash(f'Course "{new_course_name}" already exists', 'error')
                        return redirect(url_for('edit_task', task_id=task_id))
                else:
                    course_id = None
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

            db.update_task(
                task_id=task_id,
                title=title,
                course_id=course_id,
                due_date=due_date,
                description=description or None,
            )

            flash('Task updated!', 'success')
            return redirect(url_for('dashboard'))

        courses = db.get_courses()
        return render_template('tasks/edit_task.html', task=task, courses=courses)
