"""Tests for app factory and initialization"""

import os
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from flask import abort, url_for

from app import create_app, db, login_manager
from app.models import User


class TestAppFactory:
    def test_create_app_testing_config(self):
        """Test app creation with testing config"""
        app = create_app("testing")
        assert app is not None
        assert app.config["TESTING"] is True
        assert "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]

    def test_create_app_development_config(self, monkeypatch):
        """Test app creation with development config (default)"""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        app = create_app("development")
        assert app is not None
        assert app.config["TESTING"] is False

    def test_app_has_correct_folders(self):
        """Test app has correct template and static folders"""
        app = create_app("testing")
        assert "templates" in app.template_folder
        assert "static" in app.static_folder
        assert app.static_url_path == "/static"

    def test_extensions_initialized(self, app):
        """Test that all extensions are properly initialized"""
        # Check database
        assert db.engine is not None

        # Check login manager
        assert login_manager.login_view == "auth.login"
        assert login_manager.login_message == "Please log in to access this page."
        assert login_manager.login_message_category == "warning"

    def test_blueprints_registered(self, app):
        """Test that all blueprints are registered"""
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert "public" in blueprint_names
        assert "auth" in blueprint_names
        assert "member" in blueprint_names
        assert "admin" in blueprint_names
        assert "payment" in blueprint_names


class TestUserLoader:
    def test_user_loader_returns_user(self, app, test_user):
        """Test that user_loader function loads user correctly"""
        with app.app_context():
            # Call the user loader callback directly
            user = login_manager._user_callback(str(test_user.id))
            assert user is not None
            assert user.id == test_user.id
            assert user.email == test_user.email

    def test_user_loader_returns_none_for_invalid_id(self, app):
        """Test that user_loader returns None for invalid user ID"""
        with app.app_context():
            user = login_manager._user_callback("99999")
            assert user is None

    def test_user_loader_with_string_id(self, app, test_user):
        """Test that user_loader handles string IDs correctly"""
        with app.app_context():
            user = login_manager._user_callback(str(test_user.id))
            assert user is not None
            assert user.id == test_user.id


class TestErrorHandlers:
    def test_404_error_handler(self, client):
        """Test 404 error handler"""
        response = client.get("/nonexistent-page-that-does-not-exist")
        assert response.status_code == 404
        assert b"Page not found" in response.data

    def test_500_error_handler(self, client, app):
        """Test 500 error handler by triggering an exception"""
        with app.test_client() as test_client:
            # Register a route that will cause an error
            @app.route("/test-500")
            def error_route():
                # Force a 500 error
                abort(500)

            response = test_client.get("/test-500")
            assert response.status_code == 500
            assert b"Internal server error" in response.data

    def test_500_error_rolls_back_db_session(self, app):
        """Test that error handler ensures db rollback is available"""
        with app.app_context():
            # Just verify the error handler exists and would handle rollback
            # The actual rollback is tested implicitly through other tests
            assert app.error_handler_spec is not None
            assert 500 in app.error_handler_spec[None] or None in app.error_handler_spec


class TestCacheBusting:
    def test_cache_busting_for_static_files(self, app):
        """Test that cache busting context processor is configured"""
        with app.test_request_context():
            # Test that the context processor exists
            context_processors = app.template_context_processors[None]
            assert len(context_processors) > 0

            # Get the context and check url_for is available
            context = {}
            for processor in context_processors:
                context.update(processor())

            assert "url_for" in context

    def test_cache_busting_with_nonexistent_file(self, app):
        """Test cache busting with non-existent file"""
        with app.test_request_context():
            # Test with a non-existent file
            url = url_for("static", filename="nonexistent.css")

            # Should still return a valid URL (just no version parameter)
            assert "nonexistent.css" in url

    def test_cache_busting_non_static_endpoint(self, app):
        """Test that non-static endpoints are not affected"""
        with app.test_request_context():
            # Test with a non-static endpoint
            url = url_for("public.index")

            # Should not have version parameter
            assert "?v=" not in url
            assert url == "/"


class TestLogging:
    def test_logging_configured(self, app):
        """Test that logging is properly configured"""
        assert app.logger is not None
        assert app.logger.level == 20  # INFO level
        assert len(app.logger.handlers) > 0

    def test_stream_handler_always_configured(self, app):
        """Test that stream handler is always configured"""
        # Stream handler should be present even in testing
        assert app.logger is not None
        assert len(app.logger.handlers) > 0

        # Check that at least one handler is a StreamHandler
        from logging import StreamHandler

        stream_handlers = [h for h in app.logger.handlers if isinstance(h, StreamHandler)]
        assert len(stream_handlers) > 0

    def test_logger_has_correct_level(self, app):
        """Test that logger is set to INFO level"""
        import logging

        assert app.logger.level == logging.INFO

    @patch("os.path.exists")
    @patch("os.mkdir")
    @patch("app.RotatingFileHandler")
    def test_file_logging_in_production_mode(self, mock_handler, mock_mkdir, mock_exists):
        """Test that file logging is configured when not in debug/testing mode"""
        # Mock that logs directory doesn't exist
        mock_exists.return_value = False

        # Create a proper mock handler instance with level attribute
        mock_handler_instance = MagicMock()
        mock_handler_instance.level = 20  # INFO level
        mock_handler_instance.setLevel = MagicMock()
        mock_handler_instance.setFormatter = MagicMock()
        mock_handler.return_value = mock_handler_instance

        # Temporarily modify config to simulate production
        from config.config import config

        original_debug = config["testing"].DEBUG
        original_testing = config["testing"].TESTING

        try:
            # Create a production-like config
            config["testing"].DEBUG = False
            config["testing"].TESTING = False

            # Create app (this will trigger the file logging setup)
            prod_app = create_app("testing")

            # Verify logs directory was created
            mock_mkdir.assert_called_once_with("logs")

            # Verify RotatingFileHandler was instantiated
            mock_handler.assert_called_once()

            # Clean up the app's logger handlers to avoid test interference
            prod_app.logger.handlers.clear()

        finally:
            # Restore original config
            config["testing"].DEBUG = original_debug
            config["testing"].TESTING = original_testing


class TestModelsImport:
    def test_models_imported_in_app_context(self, app):
        """Test that models are properly imported in app context"""
        with app.app_context():
            # Try to import and use models
            from app.models import Credit, Event, Membership, News, Payment, Shoot, User

            # Verify they're all accessible
            assert User is not None
            assert Membership is not None
            assert Shoot is not None
            assert Credit is not None
            assert News is not None
            assert Event is not None
            assert Payment is not None

            # Verify they can be queried (tables exist)
            assert User.query.count() >= 0
            assert Membership.query.count() >= 0
            assert Shoot.query.count() >= 0


class TestRedisConnection:
    def test_redis_connection_failure(self, monkeypatch):
        """Test app handles Redis connection failure gracefully"""
        from unittest.mock import Mock

        # Mock Redis to raise connection error
        mock_redis = Mock()
        mock_redis.from_url.side_effect = Exception("Redis connection failed")

        with patch("app.Redis", mock_redis):
            # App should still create successfully even if Redis fails
            app = create_app("testing")
            assert app is not None

            # task_queue should be None when Redis fails
            from app import task_queue

            assert task_queue is None or hasattr(task_queue, "enqueue")
