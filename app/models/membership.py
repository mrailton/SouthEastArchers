from datetime import date

from app import db
from app.utils.datetime_utils import utc_now


class Membership(db.Model):
    __tablename__ = "memberships"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    start_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    initial_credits = db.Column(db.Integer, default=20, nullable=False)  # Credits from membership fee
    purchased_credits = db.Column(db.Integer, default=0, nullable=False)  # Additional purchased credits
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def is_active(self):
        return self.status == "active" and self.expiry_date >= date.today()

    def credits_remaining(self):
        """Return total credits available (initial + purchased)."""
        initial = self.initial_credits if self.initial_credits is not None else 0
        purchased = self.purchased_credits if self.purchased_credits is not None else 0
        return initial + purchased

    def use_credit(self, allow_negative: bool = False):
        """Use a credit from the membership.

        Uses initial credits first, then purchased credits.

        Args:
            allow_negative: If True, allows credits to go negative (e.g., for admin bookings)

        Returns:
            True if credit was used, False if no credits available and negative not allowed
        """
        # Ensure fields are not None
        if self.initial_credits is None:
            self.initial_credits = 0
        if self.purchased_credits is None:
            self.purchased_credits = 0

        total_credits = self.initial_credits + self.purchased_credits

        if total_credits > 0:
            # Use initial credits first
            if self.initial_credits > 0:
                self.initial_credits -= 1
            else:
                self.purchased_credits -= 1
            return True
        elif allow_negative and self.is_active():
            # Allow negative credits for active memberships (admin override)
            # Deduct from initial credits when going negative
            self.initial_credits -= 1
            return True
        return False

    def add_credits(self, amount):
        """Add purchased credits to the membership."""
        if self.purchased_credits is None:
            self.purchased_credits = 0
        self.purchased_credits += amount

    def renew(self, initial_credits: int = 20):
        """Renew the membership.

        Args:
            initial_credits: Number of initial credits to grant (default 20)
        """
        from app.services.settings_service import SettingsService

        self.start_date = date.today()
        # Calculate expiry date based on membership year settings
        self.expiry_date = SettingsService.calculate_membership_expiry(self.start_date).date()
        self.initial_credits = initial_credits
        # Keep purchased_credits as is - they don't expire
        self.status = "active"

    def expire_initial_credits(self):
        """Expire initial credits but retain purchased credits."""
        self.initial_credits = 0

    def activate(self):
        self.status = "active"

    def __repr__(self):
        return f"<Membership user_id={self.user_id} initial={self.initial_credits} purchased={self.purchased_credits}>"
