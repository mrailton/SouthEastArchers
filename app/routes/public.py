from flask import Blueprint, abort, render_template

from app.services import EventService, NewsService
from app.services.settings_service import SettingsService

bp = Blueprint("public", __name__)


@bp.get("/")
def index():
    return render_template("public/index.html")


@bp.get("/about")
def about():
    return render_template("public/about.html")


@bp.get("/news")
def news_list():
    settings = SettingsService.get()
    if not settings.news_enabled:
        abort(404)
    news = NewsService.get_published_articles()
    return render_template("public/news.html", news=news)


@bp.get("/news/<int:news_id>")
def news_detail(news_id):
    settings = SettingsService.get()
    if not settings.news_enabled:
        abort(404)
    news = NewsService.get_article_by_id(news_id)
    if not news or not news.published:
        abort(404)
    return render_template("public/news_detail.html", news=news)


@bp.get("/events")
def events():
    settings = SettingsService.get()
    if not settings.events_enabled:
        abort(404)
    events = EventService.get_upcoming_published_events()
    return render_template("public/events.html", events=events)


@bp.get("/membership")
def membership():
    return render_template("public/membership.html")
