from __future__ import annotations

from typing import TYPE_CHECKING

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.db import Model, db
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.credit import Credit
    from app.models.membership import Membership
    from app.models.payment import Payment
    from app.models.rbac import Role
    from app.models.shoot import Shoot


class User(Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    qualification: Mapped[str] = mapped_column(String(255), nullable=False, default="None")
    qualification_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    membership: Mapped[Membership | None] = relationship("Membership", backref="user", uselist=False, cascade="all, delete-orphan")
    credits: Mapped[list[Credit]] = relationship("Credit", backref="user", foreign_keys="Credit.user_id", cascade="all, delete-orphan")
    shoots: Mapped[list[Shoot]] = relationship("Shoot", secondary="user_shoots", backref="users")
    payments: Mapped[list[Payment]] = relationship("Payment", backref="user", cascade="all, delete-orphan")
    roles: Mapped[list[Role]] = relationship("Role", secondary="user_roles", back_populates="users")

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def has_active_membership(self) -> bool:
        return bool(self.membership and self.membership.is_active())

    def set_password(self, password: str) -> None:
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)

    def generate_reset_token(self) -> str:
        serializer = URLSafeTimedSerializer(get_settings().secret_key)
        return serializer.dumps(self.email, salt="password-reset-salt")

    @staticmethod
    def verify_reset_token(token: str, max_age: int = 3600) -> User | None:
        serializer = URLSafeTimedSerializer(get_settings().secret_key)
        try:
            email = serializer.loads(token, salt="password-reset-salt", max_age=max_age)
            return User.query.filter_by(email=email).first()
        except Exception:
            return None

    def has_role(self, role_name: str) -> bool:
        return any(role.name == role_name for role in self.roles)

    def permission_names(self) -> set[str]:
        return {permission.name for role in self.roles for permission in role.permissions}

    def has_permission(self, permission_name: str) -> bool:
        return permission_name in self.permission_names()

    def has_any_permission(self, *permission_names: str) -> bool:
        if not permission_names:
            return False
        user_permissions = self.permission_names()
        return any(name in user_permissions for name in permission_names)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
