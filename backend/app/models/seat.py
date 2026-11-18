from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Seat(Base):
    __tablename__ = "seat"
    __table_args__ = (
        UniqueConstraint("flight_id", "seat_no", name="uq_seat_no"),
        CheckConstraint(
            "seat_class IN ('이코노미', '비즈니스', '퍼스트')", name="ck_seat_class"
        ),
        ForeignKeyConstraint(
            ["flight_id"],
            ["flight.flight_id"],
            name="fk_seat_flight",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )

    seat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_id: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_no: Mapped[str] = mapped_column(String(5), nullable=False)
    seat_class: Mapped[str] = mapped_column(String(20), nullable=False)
    is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("TRUE")
    )
