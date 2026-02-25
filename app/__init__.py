import logging
import os
import warnings
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import AnonymousUserMixin, LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_vite_assets import ViteAssets

warnings.filterwarnings("ignore", category=SyntaxWarning, module="sumup")

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
bcrypt = Bcrypt()
vite = ViteAssets()


class AnonymousUser(AnonymousUserMixin):
    @staticmethod
    def has_permission(permission_name: str) -> bool:  # pragma: no cover - simple default
        return False

    @staticmethod
    def has_any_permission(*permission_names: str) -> bool:  # pragma: no cover - simple default
        return False


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
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    bcrypt.init_app(app)
    vite.init_app(app)

    # Setup flask login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"
    login_manager.anonymous_user = AnonymousUser

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
    from flask import render_template

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_context_processor(app: Flask) -> None:
    @app.context_processor
    def inject_now():
        return {"now": datetime.now(UTC)}

    @app.context_processor
    def inject_feature_flags():
        from app.services.settings_service import SettingsService

        try:
            settings = SettingsService.get()
            return {
                "news_enabled": settings.news_enabled,
                "events_enabled": settings.events_enabled,
            }
        except Exception:
            return {"news_enabled": False, "events_enabled": False}


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

    # Connect domain event handlers
    from app.events.handlers import connect_handlers

    connect_handlers()

    with app.app_context():
        from app.models import Credit, Event, Membership, News, Payment, Shoot, User

    return app
