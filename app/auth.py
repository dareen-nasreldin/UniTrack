from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User


def create_auth_blueprint(db):
    auth = Blueprint('auth', __name__)

    @auth.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            user_data = db.get_user_by_email(email)

            if user_data and check_password_hash(user_data['password_hash'], password):
                user = User(user_data['id'], user_data['email'],
                            user_data['password_hash'], user_data['created_at'])
                login_user(user)
                next_page = request.args.get('next', '')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))

            flash('Invalid email or password.', 'error')

        return render_template('auth/login.html')

    @auth.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            email    = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm  = request.form.get('confirm_password', '')

            if not email or '@' not in email:
                flash('A valid email address is required.', 'error')
                return redirect(url_for('auth.register'))
            if len(password) < 8:
                flash('Password must be at least 8 characters.', 'error')
                return redirect(url_for('auth.register'))
            if password != confirm:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('auth.register'))
            if db.get_user_by_email(email):
                flash('An account with that email already exists.', 'error')
                return redirect(url_for('auth.register'))

            db.create_user(email, generate_password_hash(password))
            flash('Account created — please sign in.', 'success')
            return redirect(url_for('auth.login'))

        return render_template('auth/register.html')

    @auth.route('/account')
    @login_required
    def account():
        return render_template('auth/account.html')

    @auth.route('/account/delete', methods=['POST'])
    @login_required
    def delete_account():
        user_id = current_user.id
        logout_user()
        db.delete_user(user_id)
        flash('Your account and all data have been deleted.', 'success')
        return redirect(url_for('landing'))

    @auth.route('/logout', methods=['POST'])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('landing'))

    return auth
