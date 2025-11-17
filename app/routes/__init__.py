"""Routes package"""
from .public_bp import bp as public_bp
from .auth_bp import bp as auth_bp
from .member_bp import bp as member_bp
from .payment_bp import bp as payment_bp
from .admin import bp as admin_bp

__all__ = ['public_bp', 'auth_bp', 'member_bp', 'payment_bp', 'admin_bp']
