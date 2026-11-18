from sqlalchemy import (
    CHAR,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Airport(Base):
    __tablename__ = "airport"
    __table_args__ = (
        UniqueConstraint("iata_code", name="uq_airport_iata"),
        UniqueConstraint("icao_code", name="uq_airport_icao"),
    )

    airport_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_ko: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    iata_code: Mapped[str | None] = mapped_column(CHAR(3))
    icao_code: Mapped[str | None] = mapped_column(CHAR(4))
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
