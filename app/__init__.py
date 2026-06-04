import os
from flask import Flask
from flask_login import LoginManager
from .config import config_map
from .models import User


def create_app(config_name=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static'),
    )

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app.config.from_object(config_map.get(config_name, config_map['development']))

    from .database import Database
    db = Database(app.config['DATABASE_URL'])

    # Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to continue.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        user_data = db.get_user_by_id(int(user_id))
        if user_data:
            return User(user_data['id'], user_data['email'],
                        user_data['password_hash'], user_data['created_at'])
        return None

    from .routes import register_routes
    register_routes(app, db)

    from .auth import create_auth_blueprint
    app.register_blueprint(create_auth_blueprint(db))

    @app.teardown_appcontext
    def close_db(error):
        db.close()

    return app
