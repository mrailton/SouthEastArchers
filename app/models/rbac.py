from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.db import Model
from app.db.session import Base
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.user import User

# Association tables
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("created_at", DateTime, default=utc_now, nullable=False),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
    Column("created_at", DateTime, default=utc_now, nullable=False),
)


class Role(Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    permissions: Mapped[list[Permission]] = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users: Mapped[list[User]] = relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Role {self.name}>"


class Permission(Model):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    roles: Mapped[list[Role]] = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Permission {self.name}>"


# Default RBAC seed data
PERMISSIONS: dict[str, str] = {
    "admin.dashboard.view": "Access admin dashboard",
    "settings.read": "View application settings",
    "settings.write": "Update application settings",
    "events.read": "List events",
    "events.create": "Create events",
    "events.update": "Edit events",
    "news.read": "List news articles",
    "news.create": "Create news articles",
    "news.update": "Edit news articles",
    "shoots.read": "List shoots",
    "shoots.create": "Create shoots",
    "shoots.update": "Edit shoots",
    "members.read": "View members",
    "members.create": "Create members",
    "members.update": "Edit members",
    "members.manage_membership": "Activate or renew memberships",
    "members.activate_account": "Activate user accounts",
    "payments.approve": "Approve or reject cash payments",
    "roles.manage": "Manage roles and permissions",
    "finance.read": "View financial transactions",
    "finance.create": "Create financial transactions",
    "finance.update": "Edit financial transactions",
    "finance.delete": "Delete financial transactions",
    "finance.report": "View financial statements and reports",
}

ROLE_DEFINITIONS: dict[str, dict[str, list[str] | str]] = {
    "Admin": {
        "description": "Full access to all admin features",
        "permissions": list(PERMISSIONS.keys()),
    },
    "Membership Manager": {
        "description": "Manage members, memberships, and shoots",
        "permissions": [
            "admin.dashboard.view",
            "members.read",
            "members.create",
            "members.update",
            "members.manage_membership",
            "members.activate_account",
            "payments.approve",
            "shoots.read",
            "shoots.create",
            "shoots.update",
        ],
    },
    "Content Manager": {
        "description": "Manage events and news content",
        "permissions": [
            "admin.dashboard.view",
            "events.read",
            "events.create",
            "events.update",
            "news.read",
            "news.create",
            "news.update",
        ],
    },
    "Settings Manager": {
        "description": "Manage application settings",
        "permissions": ["admin.dashboard.view", "settings.read", "settings.write"],
    },
    "Finance Manager": {
        "description": "Manage club finances and generate reports",
        "permissions": [
            "admin.dashboard.view",
            "finance.read",
            "finance.create",
            "finance.update",
            "finance.delete",
            "finance.report",
        ],
    },
}


def seed_rbac(session: Session) -> None:
    """Idempotently seed default roles and permissions."""
    existing_permissions = {p.name: p for p in session.query(Permission).all()}

    # Ensure all permissions exist
    for perm_name, description in PERMISSIONS.items():
        if perm_name not in existing_permissions:
            perm = Permission(name=perm_name, description=description)
            session.add(perm)
            existing_permissions[perm_name] = perm

    session.flush()

    # Ensure all roles exist with proper permissions
    existing_roles = {r.name: r for r in session.query(Role).all()}
    for role_name, config in ROLE_DEFINITIONS.items():
        role = existing_roles.get(role_name)
        if not role:
            raw_description = config.get("description", "")
            role = Role(
                name=role_name,
                description=raw_description if isinstance(raw_description, str) else "",
            )
            session.add(role)
            existing_roles[role_name] = role
        role_description = config.get("description")
        if isinstance(role_description, str):
            role.description = role_description

        desired_permissions = {existing_permissions[name] for name in config["permissions"]}
        role.permissions = list(desired_permissions)

    session.commit()
