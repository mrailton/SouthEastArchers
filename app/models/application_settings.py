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

    # Payment integration
    sumup_api_key = db.Column(db.String(255), default="")
    sumup_merchant_code = db.Column(db.String(100), default="")

    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return f"<ApplicationSettings id={self.id}>"
