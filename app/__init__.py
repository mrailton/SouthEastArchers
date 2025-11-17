from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
assets = None


def create_app(config_name='development'):
    """Application factory"""
    from config.config import config
    
    app = Flask(
        __name__,
        template_folder='../resources/templates',
        static_folder='../resources/static',
        static_url_path='/static'
    )
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Register blueprints
    from app.routes import public_bp, auth_bp, member_bp, admin_bp, payment_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return 'Page not found', 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return 'Internal server error', 500

    with app.app_context():
        from app.models import (
            User, Membership, Shoot, Credit, News, Event, Payment
        )

    return app
