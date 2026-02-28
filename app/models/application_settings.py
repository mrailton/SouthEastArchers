from app import db
from app.utils.datetime_utils import utc_now


class ApplicationSettings(db.Model):
    """Application-wide settings (singleton pattern - only one record should exist)."""

    __tablename__ = "application_settings"

    id = db.Column(db.Integer, primary_key=True)

    # Membership year configuration
    membership_year_start_month = db.Column(db.Integer, nullable=False, default=3)  # 1-12
    membership_year_start_day = db.Column(db.Integer, nullable=False, default=1)  # 1-31

    # Pricing (stored in cents to avoid floating point issues)
    annual_membership_cost = db.Column(db.Integer, nullable=False, default=10000)  # €100.00
    membership_shoots_included = db.Column(db.Integer, nullable=False, default=20)
    additional_shoot_cost = db.Column(db.Integer, nullable=False, default=500)  # €5.00

    # Feature toggles
    news_enabled = db.Column(db.Boolean, nullable=False, default=False)
    events_enabled = db.Column(db.Boolean, nullable=False, default=False)

    # Cash payment settings
    cash_payment_instructions = db.Column(
        db.Text,
        nullable=False,
        default="Please pay cash to a committee member at the next shoot night. Your membership/credits will be activated once payment is confirmed.",
    )

    # Visitor pricing (stored in cents)
    visitor_shoot_fee = db.Column(db.Integer, nullable=False, default=1000)  # €10.00

    # Payment processing
    sumup_fee_percentage = db.Column(db.Numeric(5, 2), nullable=True)

    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return f"<ApplicationSettings id={self.id}>"
