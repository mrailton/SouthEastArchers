from flask import Blueprint, current_app, render_template

from app import db
from app.models import Event, News
from app.utils.datetime_utils import utc_now

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    return render_template("public/index.html")


@bp.route("/about")
def about():
    return render_template("public/about.html")


@bp.route("/news")
def news_list():
    news = News.query.filter_by(published=True).order_by(News.published_at.desc()).all()
    return render_template("public/news.html", news=news)


@bp.route("/news/<int:news_id>")
def news_detail(news_id):
    from flask import abort

    news = db.session.get(News, news_id)
    if not news:
        abort(404)
    if not news.published:
        abort(404)
    return render_template("public/news_detail.html", news=news)


@bp.route("/events")
def events():
    events = Event.query.filter_by(published=True).filter(Event.start_date >= utc_now()).order_by(Event.start_date).all()
    return render_template("public/events.html", events=events)


@bp.route("/membership")
def membership():
    return render_template("public/membership.html")
