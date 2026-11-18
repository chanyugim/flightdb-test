from datetime import datetime

from pydantic import BaseModel, Field


class SimpleAirline(BaseModel):
    airline_id: int
    name_ko: str
    name_en: str
    iata_code: str | None
    icao_code: str | None


class SimpleAirport(BaseModel):
    airport_id: int
    name_ko: str
    name_en: str
    iata_code: str | None
    icao_code: str | None
    city: str
    country: str


class FlightResponse(BaseModel):
    flight_id: int
    airline: SimpleAirline
    departure_airport: SimpleAirport
    arrival_airport: SimpleAirport
    flight_status: str
    departure_at: datetime
    arrival_at: datetime
    base_price: int
    remaining_seats: int


class FlightListResponse(BaseModel):
    count: int
    total: int
    limit: int
    offset: int
    flights: list[FlightResponse]
    available_airlines: list[SimpleAirline] = Field(default_factory=list)


class RoundTripResponse(BaseModel):
    outbound: FlightResponse
    inbound: FlightResponse
    total_base_price: int


class RoundTripListResponse(BaseModel):
    count: int
    total: int
    limit: int
    offset: int
    round_trips: list[RoundTripResponse]
    available_airlines: list[SimpleAirline] = Field(default_factory=list)
