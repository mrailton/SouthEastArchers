from app.controllers.admin.events import (
    CreateEventController,
    CreateEventPostController,
    EditEventController,
    EditEventPostController,
    EventsController,
)

from . import bp

bp.add_url_rule("/events", view_func=EventsController(), endpoint="events", methods=["GET"])
bp.add_url_rule("/events/create", view_func=CreateEventController(), endpoint="create_event", methods=["GET"])
bp.add_url_rule("/events/create", view_func=CreateEventPostController(), endpoint="create_event_post", methods=["POST"])
bp.add_url_rule("/events/<int:event_id>/edit", view_func=EditEventController(), endpoint="edit_event", methods=["GET"])
bp.add_url_rule("/events/<int:event_id>/edit", view_func=EditEventPostController(), endpoint="edit_event_post", methods=["POST"])
