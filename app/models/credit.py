from app import db
from app.utils.datetime_utils import utc_now


class Credit(db.Model):
    __tablename__ = "credits"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    amount = db.Column(db.Integer, default=1)
    payment_id = db.Column(db.Integer, db.ForeignKey("payments.id"), nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<Credit user_id={self.user_id} amount={self.amount}>"
