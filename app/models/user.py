from __future__ import annotations

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer

from app import bcrypt, db
from app.utils.datetime_utils import utc_now


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    qualification = db.Column(db.String(255), nullable=False, default="None")
    qualification_detail = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    membership = db.relationship("Membership", backref="user", uselist=False, cascade="all, delete-orphan")
    credits = db.relationship("Credit", backref="user", cascade="all, delete-orphan")
    shoots = db.relationship("Shoot", secondary="user_shoots", backref="users")
    payments = db.relationship("Payment", backref="user", cascade="all, delete-orphan")
    roles = db.relationship("Role", secondary="user_roles", back_populates="users")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return serializer.dumps(self.email, salt="password-reset-salt")

    @staticmethod
    def verify_reset_token(token, max_age=3600):
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
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

    def __repr__(self):
        return f"<User {self.email}>"
