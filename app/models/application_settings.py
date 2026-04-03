from app import db
from app.utils.datetime_utils import utc_now


class Setting(db.Model):
    """Key-value application settings."""

    __tablename__ = "setting"

    key = db.Column(db.String(128), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<Setting {self.key}={self.value!r}>"
