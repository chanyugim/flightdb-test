from sqlalchemy import (
    CHAR,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Airline(Base):
    __tablename__ = "airline"
    __table_args__ = (
        UniqueConstraint("iata_code", name="uq_airline_iata"),
        UniqueConstraint("icao_code", name="uq_airline_icao"),
    )

    airline_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_ko: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    iata_code: Mapped[str | None] = mapped_column(CHAR(2))
    icao_code: Mapped[str | None] = mapped_column(CHAR(3))
    country: Mapped[str] = mapped_column(String(50), nullable=False)
