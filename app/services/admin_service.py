from datetime import date, timedelta

from app.models import Membership, User


class AdminService:

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Get statistics for the admin dashboard."""
        total_members = User.query.count()
        active_memberships = Membership.query.filter_by(status="active").count()

        today = date.today()
        expiry_threshold = today + timedelta(days=30)
        expiring_soon = Membership.query.filter(
            Membership.status == "active",
            Membership.expiry_date <= expiry_threshold,
            Membership.expiry_date >= today,
        ).count()

        recent_members = User.query.order_by(User.created_at.desc()).limit(5).all()

        return {
            "total_members": total_members,
            "active_memberships": active_memberships,
            "expiring_soon": expiring_soon,
            "recent_members": recent_members,
        }
