from __future__ import annotations

from datetime import datetime

from app import db

# Association tables
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow, nullable=False),
)

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow, nullable=False),
)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = db.relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Role {self.name}>"


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    roles = db.relationship("Role", secondary=role_permissions, back_populates="permissions")

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
    "roles.manage": "Manage roles and permissions",
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
}


def seed_rbac(session) -> None:
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
            role = Role(name=role_name, description=config.get("description", ""))
            session.add(role)
            existing_roles[role_name] = role
        if config.get("description"):
            role.description = config["description"]

        desired_permissions = {existing_permissions[name] for name in config["permissions"]}
        role.permissions = list(desired_permissions)

    session.commit()
