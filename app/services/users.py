from __future__ import annotations

import logging
from datetime import date

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.db import Pagination
from app.events import user_activated
from app.models.credit import Credit
from app.models.membership import Membership
from app.models.payment import Payment
from app.models.rbac import Role
from app.models.user import User
from app.repositories import CreditRepository, MembershipRepository, RBACRepository, UserRepository
from app.services import settings
from app.services.result import ServiceResult

logger = logging.getLogger(__name__)


def get_user_by_id(user_id: int, db: Session | None = None) -> User | None:
    if db is not None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
                selectinload(User.membership),
                selectinload(User.shoots),
            )
        )
        return db.execute(stmt).scalar_one_or_none()
    return UserRepository.get_by_id(user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_all_users_paginated(
    page: int = 1,
    per_page: int = 20,
    search: str = "",
    membership_filter: str = "all",
) -> Pagination:
    return UserRepository.get_all_paginated(page=page, per_page=per_page, search=search, membership_filter=membership_filter)


def create_user(
    *,
    name: str,
    email: str,
    password: str,
    phone: str | None = None,
    qualification: str = "none",
    qualification_detail: str | None = None,
    db: Session | None = None,
) -> ServiceResult[User]:
    if db is not None:
        if get_user_by_email(db, email):
            return ServiceResult.fail("Email already registered.")
        user = User(
            name=name,
            email=email,
            phone=phone or None,
            qualification=qualification,
            qualification_detail=None if qualification in (None, "none", "None") else (qualification_detail or None),
            is_active=False,
            password_hash=hash_password(password),
        )
        try:
            db.add(user)
            db.flush()
            return ServiceResult.ok(data=user)
        except Exception as exc:
            logger.exception("Error creating user")
            return ServiceResult.fail(f"An error occurred during registration: {exc}")

    if UserRepository.get_by_email(email):
        return ServiceResult.fail("Email already registered.")
    user = User(
        name=name,
        email=email,
        phone=phone,
        qualification=qualification,
        qualification_detail=None if qualification in (None, "none", "None") else (qualification_detail or None),
        is_active=False,
    )
    user.set_password(password)
    try:
        UserRepository.add(user)
        UserRepository.save()
        return ServiceResult.ok(data=user)
    except Exception as exc:
        logger.error("Error creating user: %s", exc)
        return ServiceResult.fail("An error occurred during registration.")


def generate_reset_token(email: str) -> str:
    serializer = URLSafeTimedSerializer(get_settings().secret_key)
    return serializer.dumps(email, salt="password-reset-salt")


def verify_reset_token(db: Session, token: str, max_age: int = 86400) -> User | None:
    serializer = URLSafeTimedSerializer(get_settings().secret_key)
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=max_age)
        return get_user_by_email(db, str(email))
    except Exception:
        return None


def create_password_reset_token(user: User) -> str:
    return user.generate_reset_token()  # type: ignore[no-any-return]


def reset_password(token: str, new_password: str, *, db: Session | None = None) -> ServiceResult[None]:
    if db is not None:
        user = verify_reset_token(db, token)
        if not user:
            return ServiceResult.fail("Invalid or expired reset link.")
        user.password_hash = hash_password(new_password)
        return ServiceResult.ok(message="Password reset successfully.")

    user = User.verify_reset_token(token, max_age=86400)
    if not user:
        return ServiceResult.fail("Invalid or expired reset link.")
    user.set_password(new_password)
    UserRepository.save()
    return ServiceResult.ok(message="Password reset successfully.")


class SimplePagination:
    def __init__(self, items: list, *, page: int, per_page: int, total: int):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total

    @property
    def prev_num(self) -> int | None:
        return self.page - 1 if self.page > 1 else None

    @property
    def next_num(self) -> int | None:
        return self.page + 1 if self.page * self.per_page < self.total else None

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.per_page - 1) // self.per_page)


def update_profile(
    user: User,
    *,
    name: str | None = None,
    phone: str | None = None,
    db: Session | None = None,
) -> ServiceResult[None]:
    if name:
        user.name = name
    if phone is not None:
        user.phone = phone if db is None else (phone or None)
    if db is not None:
        return ServiceResult.ok(message="Profile updated successfully!")
    try:
        UserRepository.save()
        return ServiceResult.ok(message="Profile updated successfully!")
    except Exception as exc:
        logger.error("Error updating profile: %s", exc)
        return ServiceResult.fail("An error occurred while updating profile.")


def change_password(
    user: User,
    *,
    current_password: str,
    new_password: str,
    db: Session | None = None,
) -> ServiceResult[None]:
    if db is not None:
        if not verify_password(current_password, user.password_hash):
            return ServiceResult.fail("Current password is incorrect.")
        if len(new_password) < 8:
            return ServiceResult.fail("New password must be at least 8 characters long.")
        user.password_hash = hash_password(new_password)
        return ServiceResult.ok(message="Password changed successfully!")

    if not user.check_password(current_password):
        return ServiceResult.fail("Current password is incorrect.")
    if len(new_password) < 8:
        return ServiceResult.fail("New password must be at least 8 characters long.")
    user.set_password(new_password)
    try:
        UserRepository.save()
        return ServiceResult.ok(message="Password changed successfully!")
    except Exception as exc:
        logger.error("Error changing password: %s", exc)
        return ServiceResult.fail("An error occurred while changing password.")


def authenticate(email: str, password: str, *, db: Session | None = None) -> User | None:
    if db is not None:
        user = get_user_by_email(db, email)
        if user and verify_password(password, user.password_hash):
            return user
        return None
    user = UserRepository.get_by_email(email)
    if user and user.check_password(password):
        return user
    return None


def get_user_payments_paginated(db: Session, user_id: int, *, page: int = 1, per_page: int = 5) -> SimplePagination:
    total = db.scalar(select(func.count()).select_from(Payment).where(Payment.user_id == user_id)) or 0
    items = list(
        db.scalars(select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc()).offset((page - 1) * per_page).limit(per_page)).all()
    )
    return SimplePagination(items, page=page, per_page=per_page, total=total)


def create_member(
    name: str,
    email: str,
    phone: str | None = None,
    password: str = "changeme123",
    role_ids: list[int] | None = None,
    create_membership: bool = False,
    qualification: str = "none",
) -> ServiceResult[User]:
    if UserRepository.get_by_email(email):
        return ServiceResult.fail("Email already registered.")

    user = User(name=name, email=email, phone=phone, qualification=qualification, is_active=False)
    user.set_password(password)

    try:
        UserRepository.add(user)
        UserRepository.flush()

        if role_ids:
            roles = RBACRepository.get_roles_by_ids(role_ids)
            user.roles = roles  # type: ignore[assignment]

        if create_membership:
            start = date.today()
            membership = Membership(
                user_id=user.id,
                start_date=start,
                expiry_date=settings.calculate_membership_expiry(start).date(),
                initial_credits=20,
                purchased_credits=0,
                status="active",
            )
            MembershipRepository.add(membership)

        UserRepository.save()
        return ServiceResult.ok(data=user)
    except Exception as exc:
        logger.error("Error creating member: %s", exc)
        return ServiceResult.fail("An error occurred while creating member.")


def update_member(
    user: User,
    name: str,
    email: str,
    phone: str | None = None,
    qualification: str | None = None,
    qualification_detail: str | None = None,
    role_ids: list[int] | None = None,
    is_active: bool = True,
    password: str | None = None,
    membership_start_date: date | None = None,
    membership_expiry_date: date | None = None,
    membership_initial_credits: int | None = None,
    membership_purchased_credits: int | None = None,
) -> ServiceResult[None]:
    user.name = name
    user.email = email
    user.phone = phone
    if qualification:
        user.qualification = qualification
    user.qualification_detail = None if qualification == "none" else (qualification_detail or None)
    if role_ids is not None:
        roles = RBACRepository.get_roles_by_ids(role_ids)
        user.roles = roles  # type: ignore[assignment]
    user.is_active = is_active

    if password:
        user.set_password(password)

    if user.membership:
        if membership_start_date:
            user.membership.start_date = membership_start_date  # type: ignore[attr-defined]
        if membership_expiry_date:
            user.membership.expiry_date = membership_expiry_date  # type: ignore[attr-defined]
        if membership_initial_credits is not None:
            user.membership.initial_credits = membership_initial_credits  # type: ignore[attr-defined]
        if membership_purchased_credits is not None:
            user.membership.purchased_credits = membership_purchased_credits  # type: ignore[attr-defined]

    try:
        UserRepository.save()
        return ServiceResult.ok(message=f"Member {user.name} updated successfully!")
    except Exception as exc:
        logger.error("Error updating member: %s", exc)
        return ServiceResult.fail("An error occurred while updating member.")


def activate_account(user_id: int) -> ServiceResult[User]:
    member = UserRepository.get_by_id(user_id)
    if not member:
        return ServiceResult.fail("User not found.")
    if member.is_active:
        return ServiceResult.fail(f"{member.name}'s account is already active.")
    member.is_active = True
    UserRepository.save()
    try:
        user_activated.send(user_id=user_id)
    except Exception:
        pass
    return ServiceResult.ok(data=member, message=f"Account activated for {member.name}! Welcome email sent.")


def adjust_member_credits(
    member: User,
    *,
    admin_user_id: int,
    quantity: int,
    action: str,
    reason: str,
) -> ServiceResult[None]:
    if not member.membership:
        return ServiceResult.fail("Member does not have a membership.")
    if quantity < 1:
        return ServiceResult.fail("Please enter a valid number of credits (minimum 1).")
    if action == "remove":
        member.membership.remove_credits(quantity)
        signed_amount = -quantity
        verb = "Removed"
        preposition = "from"
    else:
        member.membership.add_credits(quantity)
        signed_amount = quantity
        verb = "Added"
        preposition = "to"
    CreditRepository.add(
        Credit(
            user_id=member.id,
            amount=signed_amount,
            payment_id=None,
            reason=reason,
            adjusted_by_id=admin_user_id,
        )
    )
    CreditRepository.save()
    return ServiceResult.ok(message=f"{verb} {quantity} credit(s) {preposition} {member.name}'s account.")
