from flask import Blueprint

from app.controllers.public import (
    AboutController,
    EventsController,
    IndexController,
    MembershipController,
    NewsDetailController,
    NewsListController,
)

bp = Blueprint("public", __name__)

bp.add_url_rule("/", view_func=IndexController(), endpoint="index", methods=["GET"])
bp.add_url_rule("/about", view_func=AboutController(), endpoint="about", methods=["GET"])
bp.add_url_rule("/news", view_func=NewsListController(), endpoint="news_list", methods=["GET"])
bp.add_url_rule("/news/<int:news_id>", view_func=NewsDetailController(), endpoint="news_detail", methods=["GET"])
bp.add_url_rule("/events", view_func=EventsController(), endpoint="events", methods=["GET"])
bp.add_url_rule("/membership", view_func=MembershipController(), endpoint="membership", methods=["GET"])
