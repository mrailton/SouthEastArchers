from flask import Blueprint, render_template, current_app
from app.models import News, Event
from app.utils.datetime_utils import utc_now
from datetime import datetime

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    """Home page"""
    return render_template('public/index.html')


@bp.route('/about')
def about():
    """About page"""
    return render_template('public/about.html')


@bp.route('/news')
def news_list():
    """News list page"""
    news = News.query.filter_by(published=True).order_by(News.published_at.desc()).all()
    return render_template('public/news.html', news=news)


@bp.route('/news/<int:news_id>')
def news_detail(news_id):
    """News detail page"""
    news = db.session.get(News, news_id)
    if not news:
        from flask import abort
        abort(404)
    if not news.published:
        return render_template('errors/404.html'), 404
    return render_template('public/news_detail.html', news=news)


@bp.route('/events')
def events():
    """Events list page"""
    events = Event.query.filter_by(published=True).filter(
        Event.start_date >= utc_now()
    ).order_by(Event.start_date).all()
    return render_template('public/events.html', events=events)


@bp.route('/membership')
def membership():
    """Membership information page"""
    return render_template('public/membership.html')
