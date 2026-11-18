from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.validation import BusinessDateTime, RequestModel

FlightStatus = Literal["예정", "지연", "결항", "완료"]
SeatClass = Literal["이코노미", "비즈니스", "퍼스트"]


class AdminSummaryResponse(BaseModel):
    members: int
    flights: int
    confirmed_reservations: int
    pending_inquiries: int


class FlightCreateRequest(RequestModel):
    airline_id: int
    departure_airport_id: int
    arrival_airport_id: int
    flight_status: FlightStatus = "예정"
    departure_at: BusinessDateTime
    arrival_at: BusinessDateTime
    base_price: int = Field(ge=0)


class FlightUpdateRequest(RequestModel):
    flight_status: FlightStatus | None = None
    departure_at: BusinessDateTime | None = None
    arrival_at: BusinessDateTime | None = None
    base_price: int | None = Field(default=None, ge=0)


class SeatCreateItem(RequestModel):
    seat_no: str = Field(min_length=1, max_length=5, pattern=r"^[0-9]{1,3}[A-Za-z]$")
    seat_class: SeatClass


class SeatBulkCreateRequest(RequestModel):
    seats: list[SeatCreateItem] = Field(min_length=1, max_length=500)


class PromotionCreateRequest(RequestModel):
    promotion_name: str = Field(min_length=1, max_length=50)
    discount_rate: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    start_at: BusinessDateTime
    end_at: BusinessDateTime


class PromotionUpdateRequest(RequestModel):
    promotion_name: str | None = Field(default=None, min_length=1, max_length=50)
    discount_rate: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2
    )
    start_at: BusinessDateTime | None = None
    end_at: BusinessDateTime | None = None
