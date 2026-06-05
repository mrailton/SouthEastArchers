from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db import Model, db
from app.utils.datetime_utils import utc_now


class Credit(Model):
    __tablename__ = "credits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, default=1)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    reason = Column(String(255), nullable=True)
    adjusted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    adjusted_by = relationship("User", foreign_keys=[adjusted_by_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<Credit user_id={self.user_id} amount={self.amount}>"
