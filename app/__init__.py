import os
from flask import Flask
from .config import config_map


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
    db = Database(app.config['DATABASE_PATH'])

    from .routes import register_routes
    register_routes(app, db)

    @app.teardown_appcontext
    def close_db(error):
        db.close()

    return app
