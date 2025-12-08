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
    date_of_birth = db.Column(db.Date, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    membership = db.relationship("Membership", backref="user", uselist=False, cascade="all, delete-orphan")
    credits = db.relationship("Credit", backref="user", cascade="all, delete-orphan")
    shoots = db.relationship("Shoot", secondary="user_shoots", backref="users")
    payments = db.relationship("Payment", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_age(self):
        from datetime import date

        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

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

    def __repr__(self):
        return f"<User {self.email}>"
