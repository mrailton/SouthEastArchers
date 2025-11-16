from datetime import datetime, timedelta
from app import db
from app.utils.datetime_utils import utc_now


class Membership(db.Model):
    """Membership model to track user membership status and renewal"""
    __tablename__ = 'memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    start_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    nights_used = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('active', 'expired', 'cancelled'), default='active')
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    def is_active(self):
        """Check if membership is currently active"""
        from datetime import date
        return self.status == 'active' and self.expiry_date >= date.today()
    
    def nights_remaining(self):
        """Get remaining nights in annual membership"""
        from config.config import Config
        return max(0, Config.MEMBERSHIP_NIGHTS_INCLUDED - self.nights_used)
    
    def renew(self):
        """Renew membership for another year"""
        from datetime import date
        self.start_date = date.today()
        self.expiry_date = self.start_date + timedelta(days=365)
        self.nights_used = 0
        self.status = 'active'
    
    def __repr__(self):
        return f'<Membership user_id={self.user_id} status={self.status}>'
