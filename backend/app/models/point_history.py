from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKeyConstraint,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PointHistory(Base):
    __tablename__ = "point_history"
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('적립', '사용', '회수', '반환')", name="ck_point_type"
        ),
        CheckConstraint("change_amount >= 0", name="ck_point_amount"),
        CheckConstraint("balance_after >= 0", name="ck_point_balance"),
        ForeignKeyConstraint(
            ["reservation_no"],
            ["reservation.reservation_no"],
            name="fk_point_reservation",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )

    point_history_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reservation_no: Mapped[str] = mapped_column(String(20), nullable=False)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    change_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
