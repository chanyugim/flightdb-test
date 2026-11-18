from datetime import date

from sqlalchemy import Date, ForeignKeyConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReservationDetail(Base):
    __tablename__ = "reservation_detail"
    __table_args__ = (
        UniqueConstraint(
            "reservation_no", "seat_id", name="uq_detail_reservation_seat"
        ),
        ForeignKeyConstraint(
            ["reservation_no"],
            ["reservation.reservation_no"],
            name="fk_detail_reservation",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["seat_id"],
            ["seat.seat_id"],
            name="fk_detail_seat",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )

    reservation_detail_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reservation_no: Mapped[str] = mapped_column(String(20), nullable=False)
    seat_id: Mapped[int] = mapped_column(Integer, nullable=False)
    passenger_name: Mapped[str] = mapped_column(String(30), nullable=False)
    passenger_birth_date: Mapped[date] = mapped_column(Date, nullable=False)
