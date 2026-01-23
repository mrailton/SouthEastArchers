import logging
import os
import warnings
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

warnings.filterwarnings("ignore", category=SyntaxWarning, module="sumup")

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
bcrypt = Bcrypt()


def _configure_logging(app: Flask) -> None:
    """Configure file and stream logging for the app."""
    # File handler (only when not debug/testing)
    if not app.debug and not app.testing:
        if not os.path.exists("logs"):
            os.mkdir("logs")

        file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Always log to stdout for Docker
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)


def _init_extensions(app: Flask) -> None:
    """Initialize flask extensions and login manager callbacks."""
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    bcrypt.init_app(app)

    # Setup flask login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    """Register the application's blueprints."""
    from app.routes import admin_bp, auth_bp, member_bp, payment_bp, public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)


def _register_error_handlers(app: Flask) -> None:
    """Register generic error handlers."""

    @app.errorhandler(404)
    def not_found(e):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return "Internal server error", 500


def _register_context_processor(app: Flask) -> None:
    """Register context processor for cache-busted static assets and vite helpers."""

    @app.context_processor
    def override_url_for():
        from flask import url_for as flask_url_for

        from app.utils.vite import vite_asset, vite_hmr_client

        def dated_url_for(endpoint, **values):
            if endpoint == "static":
                filename = values.get("filename", None)
                if filename and app.static_folder:
                    file_path = os.path.join(app.static_folder, filename)
                    if os.path.exists(file_path):
                        values["v"] = int(os.stat(file_path).st_mtime)

            return flask_url_for(endpoint, **values)

        return dict(url_for=dated_url_for, vite_asset=vite_asset, vite_hmr_client=vite_hmr_client)


def create_app(config_name=None):
    from app.config import config

    # Determine config from environment if not specified
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        static_folder="../resources/static",
        static_url_path="/static",
    )

    # Load config
    app.config.from_object(config[config_name])

    # Configure logging and initialize extensions/blueprints
    _configure_logging(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processor(app)

    with app.app_context():
        from app.models import Credit, Event, Membership, News, Payment, Shoot, User

    return app
