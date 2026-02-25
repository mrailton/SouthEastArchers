from app.repositories import MembershipRepository, PaymentRepository, UserRepository


class AdminService:
    @staticmethod
    def get_dashboard_stats() -> dict:
        """Get statistics for the admin dashboard."""
        total_members = UserRepository.count()
        active_memberships = MembershipRepository.count_active()
        recent_members = UserRepository.get_recent(limit=5)
        count_pending_users = UserRepository.count_pending_users()

        # Pending cash payments
        pending_cash_payments = PaymentRepository.count_pending_cash()
        pending_payments_list = PaymentRepository.get_pending_cash_limited(limit=5)

        # Add user info to pending payments
        pending_payments_data = []
        for payment in pending_payments_list:
            user = UserRepository.get_by_id(payment.user_id)
            pending_payments_data.append({"payment": payment, "user": user})

        return {
            "total_members": total_members,
            "active_memberships": active_memberships,
            "recent_members": recent_members,
            "pending_cash_payments": pending_cash_payments,
            "pending_payments_data": pending_payments_data,
            "count_pending_users": count_pending_users,
        }
