from app.controllers.admin.news import (
    CreateNewsController,
    CreateNewsPostController,
    EditNewsController,
    EditNewsPostController,
    NewsController,
)

from . import bp

bp.add_url_rule("/news", view_func=NewsController(), endpoint="news", methods=["GET"])
bp.add_url_rule("/news/create", view_func=CreateNewsController(), endpoint="create_news", methods=["GET"])
bp.add_url_rule("/news/create", view_func=CreateNewsPostController(), endpoint="create_news_post", methods=["POST"])
bp.add_url_rule("/news/<int:news_id>/edit", view_func=EditNewsController(), endpoint="edit_news", methods=["GET"])
bp.add_url_rule("/news/<int:news_id>/edit", view_func=EditNewsPostController(), endpoint="edit_news_post", methods=["POST"])
