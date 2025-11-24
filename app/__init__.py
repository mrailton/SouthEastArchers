import logging
import os
import warnings
from logging.handlers import RotatingFileHandler

from flask import Flask

# Suppress SyntaxWarning from sumup library (incompatible with Python 3.14)
warnings.filterwarnings("ignore", category=SyntaxWarning, module="sumup")
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from rq import Queue

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
bcrypt = Bcrypt()
assets = None
redis_client = None
task_queue = None


def create_app(config_name="development"):
    """Application factory"""
    from config.config import config

    app = Flask(
        __name__,
        template_folder="../resources/templates",
        static_folder="../resources/static",
        static_url_path="/static",
    )

    # Load config
    app.config.from_object(config[config_name])

    # Configure logging
    if not app.debug and not app.testing:
        # File handler
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Also log to stdout for Docker
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # Initialize Redis and RQ for background jobs
    global redis_client, task_queue
    try:
        redis_client = Redis.from_url(
            app.config.get("REDIS_URL", "redis://localhost:6379/0")
        )
        task_queue = Queue(connection=redis_client, default_timeout=600)
        app.logger.info("Redis connection established for background jobs")
    except Exception as e:
        app.logger.warning(
            f"Redis connection failed: {str(e)}. Background jobs disabled."
        )
        redis_client = None
        task_queue = None

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.routes import admin_bp, auth_bp, member_bp, payment_bp, public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return "Internal server error", 500

    # Cache busting for static assets
    # Automatically appends ?v=<timestamp> to static file URLs based on file modification time
    # This ensures browsers fetch new versions when files change
    @app.context_processor
    def override_url_for():
        from flask import url_for as flask_url_for

        def dated_url_for(endpoint, **values):
            if endpoint == "static":
                filename = values.get("filename", None)
                if filename:
                    file_path = os.path.join(app.static_folder, filename)
                    if os.path.exists(file_path):
                        values["v"] = int(os.stat(file_path).st_mtime)
            return flask_url_for(endpoint, **values)

        return dict(url_for=dated_url_for)

    with app.app_context():
        from app.models import Credit, Event, Membership, News, Payment, Shoot, User

    return app
