from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, CheckConstraint, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Promotion(Base):
    __tablename__ = "promotion"
    __table_args__ = (
        CheckConstraint("discount_rate BETWEEN 0 AND 100", name="ck_promotion_rate"),
        CheckConstraint("start_at <= end_at", name="ck_promotion_period"),
    )

    promotion_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promotion_name: Mapped[str] = mapped_column(String(50), nullable=False)
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    start_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    end_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
