from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.flight import FlightResponse
from app.schemas.validation import BirthDate, RequestModel


class PassengerCreate(RequestModel):
    seat_id: int = Field(gt=0)
    passenger_name: str = Field(min_length=1, max_length=30)
    passenger_birth_date: BirthDate


class ReservationContact(RequestModel):
    promotion_id: int | None = Field(default=None, gt=0)
    booker_name: str = Field(min_length=1, max_length=30)
    booker_phone: str = Field(min_length=1, max_length=20)
    booker_email: str = Field(
        min_length=3, max_length=100, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    )
    booker_birth_date: BirthDate
    used_points: int = Field(default=0, ge=0)


class ReservationCreate(ReservationContact):
    passengers: list[PassengerCreate] = Field(min_length=1, max_length=9)


class RoundTripPassengerCreate(RequestModel):
    outbound_seat_id: int = Field(gt=0)
    inbound_seat_id: int = Field(gt=0)
    passenger_name: str = Field(min_length=1, max_length=30)
    passenger_birth_date: BirthDate


class RoundTripReservationCreate(ReservationContact):
    passengers: list[RoundTripPassengerCreate] = Field(min_length=1, max_length=9)


class ReservationDetailResponse(BaseModel):
    reservation_detail_id: int
    seat_id: int
    flight_id: int
    seat_no: str
    seat_class: str
    passenger_name: str
    passenger_birth_date: date


class ReservationSegmentResponse(BaseModel):
    direction: Literal["outbound", "inbound"]
    flight: FlightResponse
    details: list[ReservationDetailResponse]


class ReservationResponse(BaseModel):
    reservation_no: str
    member_id: str | None
    promotion_id: int | None
    booker_name: str
    booker_phone: str
    booker_email: str
    booker_birth_date: date
    used_points: int
    final_amount: int
    reserved_at: datetime
    reservation_status: str
    flight: FlightResponse | None
    trip_type: Literal["one_way", "round_trip"]
    segments: list[ReservationSegmentResponse]
    details: list[ReservationDetailResponse]


class ReservationCreatedResponse(BaseModel):
    reservation_no: str
    final_amount: int
    earned_points: int
    reservation_status: str
    trip_type: Literal["one_way", "round_trip"] = "one_way"
    idempotent_replay: bool = False


class GuestReservationLookupRequest(RequestModel):
    reservation_no: str = Field(min_length=1, max_length=20)
    booker_email: str = Field(
        min_length=3, max_length=100, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    )
    booker_phone: str = Field(min_length=1, max_length=20)


class ReservationListResponse(BaseModel):
    count: int
    total: int
    limit: int
    offset: int
    reservations: list[ReservationResponse]
