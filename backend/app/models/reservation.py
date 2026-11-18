from datetime import date, datetime

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Reservation(Base):
    __tablename__ = "reservation"
    __table_args__ = (
        CheckConstraint("used_points >= 0", name="ck_reservation_points"),
        CheckConstraint("final_amount >= 0", name="ck_reservation_amount"),
        CheckConstraint(
            "reservation_status IN ('확정', '취소')", name="ck_reservation_status"
        ),
        ForeignKeyConstraint(
            ["member_id"],
            ["member_account.member_id"],
            name="fk_reservation_member",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["promotion_id"],
            ["promotion.promotion_id"],
            name="fk_reservation_promotion",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        Index("idx_reservation_member_date", "member_id", "reserved_at"),
    )

    reservation_no: Mapped[str] = mapped_column(String(20), primary_key=True)
    member_id: Mapped[str | None] = mapped_column(String(20))
    promotion_id: Mapped[int | None] = mapped_column(Integer)
    booker_name: Mapped[str] = mapped_column(String(30), nullable=False)
    booker_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    booker_email: Mapped[str] = mapped_column(String(100), nullable=False)
    booker_birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    used_points: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    final_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    reservation_status: Mapped[str] = mapped_column(String(20), nullable=False)
