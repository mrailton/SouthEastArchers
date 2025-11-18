"""Admin routes package"""
from flask import Blueprint
from app.utils.decorators import admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')


# Import all route modules to register them with the blueprint
from . import dashboard, members, shoots, news, events
