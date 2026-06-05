from __future__ import annotations

from datetime import date
from typing import Any

from app.db import Pagination
from app.models import Shoot
from app.models.shoot import ShootLocation, ShootVisitor
from app.repositories import ShootRepository, UserRepository
from app.services import finance, settings
from app.services.result import ServiceResult


def create_shoot(
    shoot_date: date,
    location: str,
    description: str | None = None,
    attendee_ids: list[int] | None = None,
    visitors: list[dict] | None = None,
    created_by_id: int | None = None,
) -> ServiceResult[Shoot]:
    warnings: list[str] = []
    shoot = Shoot(date=shoot_date, location=ShootLocation[location], description=description)
    ShootRepository.add(shoot)

    try:
        ShootRepository.flush()

        if attendee_ids:
            _filter_shoot_attendees(attendee_ids, shoot, warnings)

        if visitors:
            _add_visitors(shoot, visitors, created_by_id)

        ShootRepository.save()
        return ServiceResult.ok(data=shoot, warnings=warnings)
    except Exception as exc:
        return ServiceResult.fail(f"Error creating shoot: {exc}")


def update_shoot(
    shoot: Shoot,
    shoot_date: date,
    location: str,
    description: str | None = None,
    attendee_ids: list[int] | None = None,
    visitors: list[dict] | None = None,
    created_by_id: int | None = None,
) -> ServiceResult[None]:
    warnings: list[str] = []
    new_attendee_ids = set(attendee_ids or [])
    old_attendee_ids = {u.id for u in shoot.users}

    removed_ids = old_attendee_ids - new_attendee_ids
    for user_id in removed_ids:
        user = UserRepository.get_by_id(user_id)
        if user and user.membership:
            user.membership.add_credits(1)

    added_ids = new_attendee_ids - old_attendee_ids
    _filter_shoot_attendees(list(added_ids), shoot, warnings)

    shoot.users = [u for u in shoot.users if u.id in new_attendee_ids]
    shoot.date = shoot_date
    shoot.location = ShootLocation[location]
    shoot.description = description

    old_visitors = {(v.name, v.club, v.affiliation, v.payment_method) for v in shoot.visitors}  # type: ignore[attr-defined]
    new_visitors = {(v["name"], v["club"], v["affiliation"], v["payment_method"]) for v in (visitors or [])}

    for visitor in list(shoot.visitors):
        key = (visitor.name, visitor.club, visitor.affiliation, visitor.payment_method)
        if key not in new_visitors:
            shoot.visitors.remove(visitor)

    added = [v for v in (visitors or []) if (v["name"], v["club"], v["affiliation"], v["payment_method"]) not in old_visitors]
    if added:
        _add_visitors(shoot, added, created_by_id)

    try:
        ShootRepository.save()
        return ServiceResult.ok(warnings=warnings)
    except Exception as exc:
        return ServiceResult.fail(f"Error updating shoot: {exc}")


def _add_visitors(shoot: Shoot, visitors: list[dict], created_by_id: int | None) -> None:
    fee_cents: int = settings.get("visitor_shoot_fee")
    sumup_fee_pct = settings.get("sumup_fee_percentage")

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
        finance.create_transaction(
            txn_type="income",
            txn_date=shoot.date,
            amount_cents=fee_cents,
            category="shoot_fees",
            description=description,
            created_by_id=by_id,
            source=source,
        )

        if v["payment_method"] == "sumup" and sumup_fee_pct is not None:
            pct = float(sumup_fee_pct)
            fee_expense_cents = int(round(fee_cents * pct / 100.0))
            finance.create_transaction(
                txn_type="expense",
                txn_date=shoot.date,
                amount_cents=fee_expense_cents,
                category="payment_processing_fees",
                description=f"SumUp fee ({pct}%) on {description}",
                created_by_id=by_id,
            )


def get_all_shoots_paginated(page: int = 1, per_page: int = 10) -> Pagination:
    return ShootRepository.get_all_paginated(page=page, per_page=per_page)


def get_shoot_by_id(shoot_id: int) -> Shoot | None:
    return ShootRepository.get_by_id(shoot_id)


def get_active_members_with_credits() -> list[tuple[int, str]]:
    active_members = UserRepository.get_active_with_membership()
    return [(u.id, f"{u.name} ({u.membership.credits_remaining()} credits)") for u in active_members if u.membership and u.membership.is_active()]


def _filter_shoot_attendees(attendee_ids: list[int], shoot: Shoot, warnings: list[Any]) -> None:
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
