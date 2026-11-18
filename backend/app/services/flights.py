from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.core.time import local_datetime, now_local
from app.models.airline import Airline
from app.services.airline_filters import excluded_airline_ids
from app.models.airport import Airport
from app.models.flight import Flight
from app.models.seat import Seat
from app.schemas.admin import (
    FlightCreateRequest,
    FlightStatus,
    FlightUpdateRequest,
    SeatBulkCreateRequest,
    SeatClass,
)


def flight_to_dict(flight, airline, departure_airport, arrival_airport):
    return {
        "flight_id": flight.flight_id,
        "airline": {
            "airline_id": airline.airline_id,
            "name_ko": airline.name_ko,
            "name_en": airline.name_en,
            "iata_code": airline.iata_code,
            "icao_code": airline.icao_code,
        },
        "departure_airport": {
            "airport_id": departure_airport.airport_id,
            "name_ko": departure_airport.name_ko,
            "name_en": departure_airport.name_en,
            "iata_code": departure_airport.iata_code,
            "icao_code": departure_airport.icao_code,
            "city": departure_airport.city,
            "country": departure_airport.country,
        },
        "arrival_airport": {
            "airport_id": arrival_airport.airport_id,
            "name_ko": arrival_airport.name_ko,
            "name_en": arrival_airport.name_en,
            "iata_code": arrival_airport.iata_code,
            "icao_code": arrival_airport.icao_code,
            "city": arrival_airport.city,
            "country": arrival_airport.country,
        },
        "flight_status": flight.flight_status,
        "departure_at": flight.departure_at,
        "arrival_at": flight.arrival_at,
        "base_price": flight.base_price,
        "remaining_seats": flight.remaining_seats,
    }


def list_admin_flights(
    db: Session, flight_status: FlightStatus | None, limit: int, offset: int
):
    departure = aliased(Airport)
    arrival = aliased(Airport)
    stmt = (
        select(Flight, Airline, departure, arrival)
        .join(Airline, Airline.airline_id == Flight.airline_id)
        .join(departure, departure.airport_id == Flight.departure_airport_id)
        .join(arrival, arrival.airport_id == Flight.arrival_airport_id)
    )
    if flight_status:
        stmt = stmt.where(Flight.flight_status == flight_status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(Flight.departure_at.desc(), Flight.flight_id)
        .offset(offset)
        .limit(limit)
    ).all()
    flights = [flight_to_dict(f, a, d, r) for f, a, d, r in rows]
    return {
        "count": len(flights),
        "total": total,
        "offset": offset,
        "limit": limit,
        "flights": flights,
    }


def create_flight(db: Session, payload: FlightCreateRequest):
    if payload.departure_airport_id == payload.arrival_airport_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Departure and arrival airports must differ",
        )
    if payload.departure_at >= payload.arrival_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="departure_at must be before arrival_at",
        )
    airline = db.get(Airline, payload.airline_id)
    departure = db.get(Airport, payload.departure_airport_id)
    arrival = db.get(Airport, payload.arrival_airport_id)
    if airline is None or departure is None or arrival is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Airline or airport not found"
        )
    flight = Flight(
        airline_id=payload.airline_id,
        departure_airport_id=payload.departure_airport_id,
        arrival_airport_id=payload.arrival_airport_id,
        flight_status=payload.flight_status,
        departure_at=payload.departure_at,
        arrival_at=payload.arrival_at,
        base_price=payload.base_price,
        remaining_seats=0,
    )
    db.add(flight)
    db.commit()
    db.refresh(flight)
    return flight_to_dict(flight, airline, departure, arrival)


def update_flight(db: Session, flight_id: int, payload: FlightUpdateRequest):
    flight = db.scalar(
        select(Flight)
        .where(Flight.flight_id == flight_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if flight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    departure_at = (
        payload.departure_at
        if payload.departure_at is not None
        else flight.departure_at
    )
    arrival_at = (
        payload.arrival_at if payload.arrival_at is not None else flight.arrival_at
    )
    if departure_at >= arrival_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="departure_at must be before arrival_at",
        )
    if payload.flight_status is not None:
        flight.flight_status = payload.flight_status
    if payload.departure_at is not None:
        flight.departure_at = payload.departure_at
    if payload.arrival_at is not None:
        flight.arrival_at = payload.arrival_at
    if payload.base_price is not None:
        flight.base_price = payload.base_price
    db.commit()
    db.refresh(flight)
    airline = db.get(Airline, flight.airline_id)
    departure = db.get(Airport, flight.departure_airport_id)
    arrival = db.get(Airport, flight.arrival_airport_id)
    return flight_to_dict(flight, airline, departure, arrival)


def list_admin_flight_seats(db: Session, flight_id: int):
    if db.get(Flight, flight_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    seats = db.scalars(
        select(Seat).where(Seat.flight_id == flight_id).order_by(Seat.seat_no)
    ).all()
    return {"count": len(seats), "seats": seats}


def create_flight_seats(db: Session, flight_id: int, payload: SeatBulkCreateRequest):
    flight = db.scalar(
        select(Flight).where(Flight.flight_id == flight_id).with_for_update()
    )
    if flight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
        )
    requested = [s.seat_no.upper() for s in payload.seats]
    if len(requested) != len(set(requested)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate seat_no in request",
        )
    existing = set(
        db.scalars(
            select(Seat.seat_no).where(
                Seat.flight_id == flight_id, Seat.seat_no.in_(requested)
            )
        ).all()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seat already exists: {sorted(existing)[0]}",
        )
    created = []
    for item in payload.seats:
        seat = Seat(
            flight_id=flight_id,
            seat_no=item.seat_no.upper(),
            seat_class=item.seat_class,
            is_available=True,
        )
        db.add(seat)
        created.append(seat)
    flight.remaining_seats += len(created)
    db.commit()
    for seat in created:
        db.refresh(seat)
    return {"count": len(created), "seats": created}


def search_flights(
    db: Session,
    departure: str | None,
    arrival: str | None,
    travel_date: date | None,
    airline: str | None,
    flight_status: FlightStatus | None,
    min_price: int | None,
    max_price: int | None,
    seat_class: SeatClass | None,
    departure_from: datetime | None,
    departure_to: datetime | None,
    arrival_from: datetime | None,
    arrival_to: datetime | None,
    sort_by: Literal[
        "departure_at", "arrival_at", "price", "departure_airport", "arrival_airport"
    ],
    sort_order: Literal["asc", "desc"],
    bookable_only: bool,
    limit: int,
    offset: int,
    exclude_airlines: list[str] | None = None,
    excluded_ids: list[int] | None = None,
    include_total: bool = True,
    include_airline_options: bool = False,
    departure_ids: list[int] | None = None,
    arrival_ids: list[int] | None = None,
    destinations_only: bool = False,
):
    DepartureAirport = aliased(Airport)
    ArrivalAirport = aliased(Airport)

    stmt = (
        select(Flight, Airline, DepartureAirport, ArrivalAirport)
        .join(Airline, Airline.airline_id == Flight.airline_id)
        .join(
            DepartureAirport,
            DepartureAirport.airport_id == Flight.departure_airport_id,
        )
        .join(
            ArrivalAirport,
            ArrivalAirport.airport_id == Flight.arrival_airport_id,
        )
    )

    if departure:
        code = departure.upper()
        stmt = stmt.where(
            (DepartureAirport.iata_code == code) | (DepartureAirport.icao_code == code)
        )

    if arrival:
        code = arrival.upper()
        stmt = stmt.where(
            (ArrivalAirport.iata_code == code) | (ArrivalAirport.icao_code == code)
        )

    if travel_date:
        start = datetime.combine(travel_date, time.min)
        end = start + timedelta(days=1)
        stmt = stmt.where(
            Flight.departure_at >= start,
            Flight.departure_at < end,
        )

    if departure_ids is not None:
        stmt = stmt.where(Flight.departure_airport_id.in_(departure_ids))
    if arrival_ids is not None:
        stmt = stmt.where(Flight.arrival_airport_id.in_(arrival_ids))

    if flight_status:
        stmt = stmt.where(Flight.flight_status == flight_status)

    if min_price is not None:
        stmt = stmt.where(Flight.base_price >= min_price)

    if max_price is not None:
        stmt = stmt.where(Flight.base_price <= max_price)

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=400, detail="min_price must not exceed max_price"
        )
    for column, lower, upper in (
        (Flight.departure_at, departure_from, departure_to),
        (Flight.arrival_at, arrival_from, arrival_to),
    ):
        lower = local_datetime(lower) if lower is not None else None
        upper = local_datetime(upper) if upper is not None else None
        if lower is not None and upper is not None and lower > upper:
            raise HTTPException(status_code=400, detail="Invalid datetime range")
        if lower is not None:
            stmt = stmt.where(column >= lower)
        if upper is not None:
            stmt = stmt.where(column <= upper)
    if bookable_only:
        stmt = stmt.where(
            Flight.flight_status.in_(["예정", "지연"]),
            Flight.departure_at > now_local(),
            Flight.remaining_seats > 0,
        )
    if seat_class is not None:
        seats = select(Seat.seat_id).where(
            Seat.flight_id == Flight.flight_id, Seat.seat_class == seat_class
        )
        if bookable_only:
            seats = seats.where(Seat.is_available.is_(True))
        stmt = stmt.where(seats.exists())
    available_airlines = []
    if include_airline_options:
        matching_airlines = stmt.with_only_columns(Flight.airline_id)
        carriers = db.scalars(select(Airline).where(Airline.airline_id.in_(matching_airlines)).order_by(Airline.name_ko, Airline.airline_id)).all()
        available_airlines = [{"airline_id": a.airline_id, "name_ko": a.name_ko, "name_en": a.name_en, "iata_code": a.iata_code, "icao_code": a.icao_code} for a in carriers]
    excluded = (
        excluded_ids
        if excluded_ids is not None
        else excluded_airline_ids(db, exclude_airlines, airline)
    )
    if excluded:
        stmt = stmt.where(Flight.airline_id.not_in(excluded))
    if airline:
        code = airline.upper()
        stmt = stmt.where((Airline.iata_code == code) | (Airline.icao_code == code))

    if destinations_only:
        matching_ids = stmt.with_only_columns(Flight.arrival_airport_id)
        airports = db.scalars(
            select(Airport)
            .where(Airport.airport_id.in_(matching_ids))
            .order_by(Airport.name_ko, Airport.airport_id)
            .offset(offset)
            .limit(limit)
        ).all()
        return {"count": len(airports), "destinations": airports}
    total = (
        (db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        if include_total
        else None
    )
    sort_column = {
        "departure_at": Flight.departure_at,
        "arrival_at": Flight.arrival_at,
        "price": Flight.base_price,
        "departure_airport": DepartureAirport.name_en,
        "arrival_airport": ArrivalAirport.name_en,
    }[sort_by]
    ordering = sort_column.desc() if sort_order == "desc" else sort_column.asc()
    stmt = stmt.order_by(ordering, Flight.flight_id).offset(offset).limit(limit)
    rows = db.execute(stmt).all()

    flights = [flight_to_dict(f, a, dep, arr) for f, a, dep, arr in rows]

    return {
        "count": len(flights),
        "total": total,
        "offset": offset,
        "limit": limit,
        "flights": flights,
        "available_airlines": available_airlines,
    }


def get_flight(db: Session, flight_id: int):
    DepartureAirport = aliased(Airport)
    ArrivalAirport = aliased(Airport)

    stmt = (
        select(Flight, Airline, DepartureAirport, ArrivalAirport)
        .join(Airline, Airline.airline_id == Flight.airline_id)
        .join(
            DepartureAirport,
            DepartureAirport.airport_id == Flight.departure_airport_id,
        )
        .join(
            ArrivalAirport,
            ArrivalAirport.airport_id == Flight.arrival_airport_id,
        )
        .where(Flight.flight_id == flight_id)
    )

    row = db.execute(stmt).first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found",
        )

    return flight_to_dict(*row)


def get_flight_seats(
    db: Session, flight_id: int, available_only: bool, seat_class: SeatClass | None
):
    flight_exists = db.scalar(
        select(Flight.flight_id).where(Flight.flight_id == flight_id)
    )

    if flight_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found",
        )

    stmt = select(Seat).where(Seat.flight_id == flight_id)

    if available_only:
        stmt = stmt.where(Seat.is_available.is_(True))

    if seat_class:
        stmt = stmt.where(Seat.seat_class == seat_class)

    stmt = stmt.order_by(Seat.seat_class, Seat.seat_no)
    seats = db.scalars(stmt).all()

    return {"count": len(seats), "seats": seats}
