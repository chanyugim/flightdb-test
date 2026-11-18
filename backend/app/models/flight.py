from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Flight(Base):
    __tablename__ = "flight"
    __table_args__ = (
        CheckConstraint(
            "departure_airport_id <> arrival_airport_id", name="ck_flight_airports"
        ),
        CheckConstraint("departure_at < arrival_at", name="ck_flight_time"),
        CheckConstraint("base_price >= 0", name="ck_flight_price"),
        CheckConstraint("remaining_seats >= 0", name="ck_flight_seats"),
        CheckConstraint(
            "flight_status IN ('예정', '지연', '결항', '완료')", name="ck_flight_status"
        ),
        ForeignKeyConstraint(
            ["airline_id"],
            ["airline.airline_id"],
            name="fk_flight_airline",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["departure_airport_id"],
            ["airport.airport_id"],
            name="fk_flight_departure",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["arrival_airport_id"],
            ["airport.airport_id"],
            name="fk_flight_arrival",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        Index(
            "idx_flight_route_time",
            "departure_airport_id",
            "arrival_airport_id",
            "departure_at",
        ),
    )

    flight_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airline_id: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_airport_id: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_airport_id: Mapped[int] = mapped_column(Integer, nullable=False)
    flight_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'예정'")
    )
    departure_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    arrival_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    base_price: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_seats: Mapped[int] = mapped_column(Integer, nullable=False)
