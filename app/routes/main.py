from flask import Blueprint, render_template
from app.models import News, Event
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    latest_news = News.query.filter_by(published=True).order_by(News.created_at.desc()).limit(3).all()
    upcoming_events = Event.query.filter_by(published=True).filter(Event.event_date >= datetime.utcnow()).order_by(Event.event_date).limit(3).all()
    return render_template('index.html', news=latest_news, events=upcoming_events)

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/news')
def news():
    all_news = News.query.filter_by(published=True).order_by(News.created_at.desc()).all()
    return render_template('news.html', news=all_news)

@bp.route('/news/<int:id>')
def news_detail(id):
    news_item = News.query.get_or_404(id)
    return render_template('news_detail.html', news=news_item)

@bp.route('/events')
def events():
    upcoming = Event.query.filter_by(published=True).filter(Event.event_date >= datetime.utcnow()).order_by(Event.event_date).all()
    return render_template('events.html', events=upcoming)

@bp.route('/events/<int:id>')
def event_detail(id):
    event = Event.query.get_or_404(id)
    return render_template('event_detail.html', event=event)
