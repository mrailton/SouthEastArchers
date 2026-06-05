from __future__ import annotations

import logging

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.payment import Payment
from app.models.rbac import Role
from app.models.user import User
from app.services.result import ServiceResult

logger = logging.getLogger(__name__)


def get_user_by_id(db: Session, user_id: int) -> User | None:
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


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user and verify_password(password, user.password_hash):
        return user
    return None


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    phone: str | None = None,
    qualification: str = "none",
    qualification_detail: str | None = None,
) -> ServiceResult[User]:
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


def reset_password(db: Session, token: str, new_password: str) -> ServiceResult[None]:
    user = verify_reset_token(db, token)
    if not user:
        return ServiceResult.fail("Invalid or expired reset link.")
    user.password_hash = hash_password(new_password)
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
    db: Session,
    user: User,
    *,
    name: str | None = None,
    phone: str | None = None,
) -> ServiceResult[None]:
    if name:
        user.name = name
    if phone is not None:
        user.phone = phone or None
    return ServiceResult.ok(message="Profile updated successfully!")


def change_password(
    db: Session,
    user: User,
    *,
    current_password: str,
    new_password: str,
) -> ServiceResult[None]:
    if not verify_password(current_password, user.password_hash):
        return ServiceResult.fail("Current password is incorrect.")
    if len(new_password) < 8:
        return ServiceResult.fail("New password must be at least 8 characters long.")
    user.password_hash = hash_password(new_password)
    return ServiceResult.ok(message="Password changed successfully!")


def get_user_payments_paginated(db: Session, user_id: int, *, page: int = 1, per_page: int = 5) -> SimplePagination:
    total = db.scalar(select(func.count()).select_from(Payment).where(Payment.user_id == user_id)) or 0
    items = list(
        db.scalars(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).all()
    )
    return SimplePagination(items, page=page, per_page=per_page, total=total)
