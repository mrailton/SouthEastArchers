from datetime import date

from app.models import Shoot
from app.models.shoot import ShootVisitor
from app.repositories import ShootRepository, UserRepository
from app.services.finance_service import FinanceService
from app.services.settings_service import SettingsService


class ShootService:
    @staticmethod
    def create_shoot(
        shoot_date: date,
        location: str,
        description: str = None,
        attendee_ids: list[int] = None,
        visitors: list[dict] = None,
        created_by_id: int | None = None,
    ) -> tuple[Shoot | None, list[str]]:
        warnings = []
        shoot = Shoot(date=shoot_date, location=location, description=description)
        ShootRepository.add(shoot)

        try:
            ShootRepository.flush()

            if attendee_ids:
                for user_id in attendee_ids:
                    user = UserRepository.get_by_id(user_id)
                    if user and user.membership:
                        if user.membership.use_credit(allow_negative=True):
                            shoot.users.append(user)
                            total_credits = user.membership.credits_remaining()
                            if total_credits < 0:
                                warnings.append(f"{user.name} now has {total_credits} credits (negative balance).")
                        else:
                            warnings.append(f"{user.name} cannot be added (inactive membership).")

            if visitors:
                ShootService._add_visitors(shoot, visitors, created_by_id)

            ShootRepository.save()
            return shoot, warnings
        except Exception as e:
            return None, [f"Error creating shoot: {str(e)}"]

    @staticmethod
    def update_shoot(
        shoot: Shoot,
        shoot_date: date,
        location: str,
        description: str = None,
        attendee_ids: list[int] = None,
        visitors: list[dict] = None,
        created_by_id: int | None = None,
    ) -> tuple[bool, list[str]]:
        warnings = []
        new_attendee_ids = set(attendee_ids or [])
        old_attendee_ids = {u.id for u in shoot.users}

        removed_ids = old_attendee_ids - new_attendee_ids
        for user_id in removed_ids:
            user = UserRepository.get_by_id(user_id)
            if user and user.membership:
                user.membership.add_credits(1)

        added_ids = new_attendee_ids - old_attendee_ids
        for user_id in added_ids:
            user = UserRepository.get_by_id(user_id)
            if user and user.membership:
                if user.membership.use_credit(allow_negative=True):
                    shoot.users.append(user)
                    total_credits = user.membership.credits_remaining()
                    if total_credits < 0:
                        warnings.append(f"{user.name} now has {total_credits} credits (negative balance).")
                else:
                    warnings.append(f"{user.name} cannot be added (inactive membership).")

        shoot.users = [u for u in shoot.users if u.id in new_attendee_ids]
        shoot.date = shoot_date
        shoot.location = location
        shoot.description = description

        # Handle visitors: diff old vs new to avoid duplicate transactions
        old_visitors = {(v.name, v.club, v.affiliation, v.payment_method) for v in shoot.visitors}
        new_visitors = {(v["name"], v["club"], v["affiliation"], v["payment_method"]) for v in (visitors or [])}

        # Remove visitors no longer in the list
        for visitor in list(shoot.visitors):
            key = (visitor.name, visitor.club, visitor.affiliation, visitor.payment_method)
            if key not in new_visitors:
                shoot.visitors.remove(visitor)

        # Add only genuinely new visitors (with transactions)
        added = [v for v in (visitors or []) if (v["name"], v["club"], v["affiliation"], v["payment_method"]) not in old_visitors]
        if added:
            ShootService._add_visitors(shoot, added, created_by_id)

        try:
            ShootRepository.save()
            return True, warnings
        except Exception as e:
            return False, [f"Error updating shoot: {str(e)}"]

    @staticmethod
    def _add_visitors(shoot: Shoot, visitors: list[dict], created_by_id: int | None) -> None:
        """Add visitors to a shoot and create income transactions for each."""
        settings = SettingsService.get()
        fee_cents = settings.visitor_shoot_fee
        fee_amount = fee_cents / 100.0
        sumup_fee_pct = settings.sumup_fee_percentage

        for v in visitors:
            visitor = ShootVisitor(
                name=v["name"],
                club=v["club"],
                affiliation=v["affiliation"],
                payment_method=v["payment_method"],
            )
            shoot.visitors.append(visitor)

            source = "SumUp" if v["payment_method"] == "sumup" else "Cash"
            description = f"Visitor shoot fee - {v['name']} ({v['club']})"
            by_id = created_by_id or 1
            FinanceService.create_transaction(
                txn_type="income",
                txn_date=shoot.date,
                amount=fee_amount,
                category="shoot_fees",
                description=description,
                created_by_id=by_id,
                source=source,
            )

            # Record SumUp processing fee if applicable
            if v["payment_method"] == "sumup" and sumup_fee_pct is not None:
                pct = float(sumup_fee_pct)
                fee_expense = round(fee_cents * pct / 10000.0, 2)
                FinanceService.create_transaction(
                    txn_type="expense",
                    txn_date=shoot.date,
                    amount=fee_expense,
                    category="payment_processing_fees",
                    description=f"SumUp fee ({pct}%) on {description}",
                    created_by_id=by_id,
                )

    @staticmethod
    def get_all_shoots() -> list[Shoot]:
        """Get all shoots ordered by date descending."""
        return ShootRepository.get_all()

    @staticmethod
    def get_shoot_by_id(shoot_id: int) -> Shoot | None:
        """Get a shoot by ID."""
        return ShootRepository.get_by_id(shoot_id)

    @staticmethod
    def get_active_members_with_credits() -> list[tuple[int, str]]:
        """Get active members with their credit information for form choices."""
        active_members = UserRepository.get_active_with_membership()
        return [(u.id, f"{u.name} ({u.membership.credits_remaining()} credits)") for u in active_members if u.membership and u.membership.is_active()]
