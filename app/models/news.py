from datetime import datetime
from app.utils.datetime_utils import utc_now
from app import db


class News(db.Model):
    """News articles for the club"""
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    published = db.Column(db.Boolean, default=False, index=True)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    def publish(self):
        """Publish the news article"""
        self.published = True
        self.published_at = utc_now()
    
    def __repr__(self):
        return f'<News {self.title}>'
