from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.admin import FlightStatus, SeatClass
from app.schemas.flight import FlightListResponse, FlightResponse, RoundTripListResponse
from app.schemas.seat import SeatListResponse
from app.schemas.member import RouteRecommendation
from app.services.route_stats import list_route_statistics
from app.services import flights as flights_service
from app.services.round_trips import search_round_trips as search_round_trip_service

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("", response_model=FlightListResponse)
def search_flights(
    departure: str | None = Query(default=None, min_length=3, max_length=4),
    arrival: str | None = Query(default=None, min_length=3, max_length=4),
    travel_date: date | None = Query(default=None, alias="date"),
    airline: str | None = Query(default=None, min_length=2, max_length=3),
    exclude_airlines: list[str] | None = Query(default=None, max_length=100),
    flight_status: FlightStatus | None = Query(default=None, alias="status"),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    seat_class: SeatClass | None = Query(default=None),
    departure_from: datetime | None = Query(default=None),
    departure_to: datetime | None = Query(default=None),
    arrival_from: datetime | None = Query(default=None),
    arrival_to: datetime | None = Query(default=None),
    sort_by: Literal[
        "departure_at", "arrival_at", "price", "departure_airport", "arrival_airport"
    ] = Query(default="departure_at"),
    sort_order: Literal["asc", "desc"] = Query(default="asc"),
    bookable_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_airline_options: bool = False,
    db: Session = Depends(get_db),
):
    return flights_service.search_flights(
        departure=departure,
        arrival=arrival,
        travel_date=travel_date,
        airline=airline,
        exclude_airlines=exclude_airlines,
        include_airline_options=include_airline_options,
        flight_status=flight_status,
        min_price=min_price,
        max_price=max_price,
        seat_class=seat_class,
        departure_from=departure_from,
        departure_to=departure_to,
        arrival_from=arrival_from,
        arrival_to=arrival_to,
        sort_by=sort_by,
        sort_order=sort_order,
        bookable_only=bookable_only,
        limit=limit,
        offset=offset,
        db=db,
    )


@router.get("/round-trips", response_model=RoundTripListResponse)
def search_round_trips(
    travel_date: Annotated[date, Query(alias="date")],
    db: Annotated[Session, Depends(get_db)],
    return_date: date | None = None,
    return_date_from: date | None = None,
    return_date_to: date | None = None,
    departure: Annotated[str | None, Query(min_length=3, max_length=4)] = None,
    arrival: Annotated[str | None, Query(min_length=3, max_length=4)] = None,
    airline: Annotated[str | None, Query(min_length=2, max_length=3)] = None,
    exclude_airlines: Annotated[list[str] | None, Query(max_length=100)] = None,
    min_price: Annotated[int | None, Query(ge=0)] = None,
    max_price: Annotated[int | None, Query(ge=0)] = None,
    seat_class: SeatClass | None = None,
    sort_by: Literal["price", "departure_at", "arrival_at", "return_departure_at"] = "price",
    sort_order: Literal["asc", "desc"] = "asc",
    departure_from: datetime | None = None,
    departure_to: datetime | None = None,
    arrival_from: datetime | None = None,
    arrival_to: datetime | None = None,
    return_departure_from: datetime | None = None,
    return_departure_to: datetime | None = None,
    return_arrival_from: datetime | None = None,
    return_arrival_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    include_airline_options: bool = False,
):
    return search_round_trip_service(
        db=db,
        return_departure_from=return_departure_from,
        return_departure_to=return_departure_to,
        return_arrival_from=return_arrival_from,
        return_arrival_to=return_arrival_to,
        travel_date=travel_date,
        return_date=return_date,
        return_date_from=return_date_from,
        return_date_to=return_date_to,
        departure=departure,
        arrival=arrival,
        airline=airline,
        exclude_airlines=exclude_airlines,
        include_airline_options=include_airline_options,
        min_price=min_price,
        max_price=max_price,
        seat_class=seat_class,
        sort_by=sort_by,
        sort_order=sort_order,
        departure_from=departure_from,
        departure_to=departure_to,
        arrival_from=arrival_from,
        arrival_to=arrival_to,
        limit=limit,
        offset=offset,
    )


@router.get("/popular-routes", response_model=list[RouteRecommendation])
def get_popular_routes(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=5, ge=1, le=20),
    period: Literal["rolling", "month"] = Query(default="rolling"),
    db: Session = Depends(get_db),
):
    return list_route_statistics(db, limit=limit, days=days, current_month=period == "month")


@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight(flight_id: int, db: Session = Depends(get_db)):
    return flights_service.get_flight(flight_id=flight_id, db=db)


@router.get("/{flight_id}/seats", response_model=SeatListResponse)
def get_flight_seats(
    flight_id: int,
    available_only: bool = Query(default=False),
    seat_class: SeatClass | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return flights_service.get_flight_seats(
        flight_id=flight_id, available_only=available_only, seat_class=seat_class, db=db
    )
