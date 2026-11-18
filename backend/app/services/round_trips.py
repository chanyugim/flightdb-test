from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.core.time import local_datetime, now_local
from app.models.airline import Airline
from app.services.airline_filters import excluded_airline_ids
from app.models.airport import Airport
from app.models.flight import Flight
from app.models.seat import Seat
from app.schemas.admin import SeatClass
from app.services.flights import flight_to_dict
from app.services.return_dates import resolve_return_dates


def search_round_trips(
    db: Session,
    travel_date: date,
    return_date: date | None = None,
    departure: str | None = None,
    arrival: str | None = None,
    airline: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    seat_class: SeatClass | None = None,
    sort_by: Literal["price", "departure_at", "arrival_at", "return_departure_at"] = "price",
    sort_order: Literal["asc", "desc"] = "asc",
    limit: int = 20,
    offset: int = 0,
    departure_from: datetime | None = None,
    departure_to: datetime | None = None,
    arrival_from: datetime | None = None,
    arrival_to: datetime | None = None,
    return_departure_from: datetime | None = None,
    return_departure_to: datetime | None = None,
    return_arrival_from: datetime | None = None,
    return_arrival_to: datetime | None = None,
    exclude_airlines: list[str] | None = None,
    excluded_ids: list[int] | None = None,
    include_total: bool = True,
    include_airline_options: bool = False,
    departure_ids: list[int] | None = None,
    arrival_ids: list[int] | None = None,
    return_date_from: date | None = None,
    return_date_to: date | None = None,
):
    current = now_local()
    return_start, return_end = resolve_return_dates(travel_date, return_date, return_date_from, return_date_to)
    if travel_date < current.date():
        raise HTTPException(400, "Invalid round-trip dates")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(400, "min_price must not exceed max_price")

    outbound, inbound = aliased(Flight), aliased(Flight)
    out_airline, in_airline = aliased(Airline), aliased(Airline)
    dep, arr = aliased(Airport), aliased(Airport)
    total_price = outbound.base_price + inbound.base_price
    stmt = (
        select(outbound, inbound, out_airline, in_airline, dep, arr)
        .select_from(outbound)
        .join(
            inbound,
            (inbound.departure_airport_id == outbound.arrival_airport_id)
            & (inbound.arrival_airport_id == outbound.departure_airport_id)
            & (inbound.departure_at > outbound.arrival_at),
        )
        .join(out_airline, out_airline.airline_id == outbound.airline_id)
        .join(in_airline, in_airline.airline_id == inbound.airline_id)
        .join(dep, dep.airport_id == outbound.departure_airport_id)
        .join(arr, arr.airport_id == outbound.arrival_airport_id)
    )
    for flight, day, end_day in ((outbound, travel_date, travel_date), (inbound, return_start, return_end)):
        start = datetime.combine(day, time.min)
        stmt = stmt.where(
            flight.departure_at >= start,
            flight.departure_at < datetime.combine(end_day + timedelta(days=1), time.min),
            flight.departure_at > current,
            flight.flight_status.in_(["예정", "지연"]),
            flight.remaining_seats > 0,
        )
        seats = select(Seat.seat_id).where(
            Seat.flight_id == flight.flight_id, Seat.is_available.is_(True)
        )
        if seat_class is not None:
            seats = seats.where(Seat.seat_class == seat_class)
        stmt = stmt.where(seats.exists())
    for airport, code in ((dep, departure), (arr, arrival)):
        if code:
            stmt = stmt.where(
                (airport.iata_code == code.upper())
                | (airport.icao_code == code.upper())
            )
    if departure_ids is not None:
        stmt = stmt.where(outbound.departure_airport_id.in_(departure_ids))
    if arrival_ids is not None:
        stmt = stmt.where(outbound.arrival_airport_id.in_(arrival_ids))
    if min_price is not None:
        stmt = stmt.where(total_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(total_price <= max_price)
    for column, lower, upper in (
        (outbound.departure_at, departure_from, departure_to),
        (outbound.arrival_at, arrival_from, arrival_to),
        (inbound.departure_at, return_departure_from, return_departure_to),
        (inbound.arrival_at, return_arrival_from, return_arrival_to),
    ):
        lower = local_datetime(lower) if lower else None
        upper = local_datetime(upper) if upper else None
        if lower and upper and lower > upper:
            raise HTTPException(400, "Invalid datetime range")
        if lower:
            stmt = stmt.where(column >= lower)
        if upper:
            stmt = stmt.where(column <= upper)
    available_airlines = []
    if include_airline_options:
        matching_airlines = (
            stmt.with_only_columns(outbound.airline_id)
            .union(stmt.with_only_columns(inbound.airline_id))
            .subquery("matching_airlines")
        )
        carriers = db.scalars(
            select(Airline)
            .join(matching_airlines, Airline.airline_id == matching_airlines.c.airline_id)
            .order_by(Airline.name_ko, Airline.airline_id)
        ).all()
        available_airlines = [{"airline_id": a.airline_id, "name_ko": a.name_ko, "name_en": a.name_en, "iata_code": a.iata_code, "icao_code": a.icao_code} for a in carriers]
    excluded = (
        excluded_ids
        if excluded_ids is not None
        else excluded_airline_ids(db, exclude_airlines, airline)
    )
    if excluded:
        stmt = stmt.where(
            outbound.airline_id.not_in(excluded), inbound.airline_id.not_in(excluded)
        )
    if airline:
        for carrier in (out_airline, in_airline):
            stmt = stmt.where(
                (carrier.iata_code == airline.upper())
                | (carrier.icao_code == airline.upper())
            )
    total = (
        (db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        if include_total
        else None
    )
    column = {
        "price": total_price,
        "departure_at": outbound.departure_at,
        "arrival_at": inbound.arrival_at,
        "return_departure_at": inbound.departure_at,
    }[sort_by]
    ordering = column.desc() if sort_order == "desc" else column.asc()
    rows = db.execute(
        stmt.order_by(ordering, outbound.flight_id, inbound.flight_id)
        .offset(offset)
        .limit(limit)
    ).all()
    trips = [
        {
            "outbound": flight_to_dict(out, oa, d, a),
            "inbound": flight_to_dict(back, ia, a, d),
            "total_base_price": out.base_price + back.base_price,
        }
        for out, back, oa, ia, d, a in rows
    ]
    return {
        "count": len(trips),
        "total": total,
        "limit": limit,
        "offset": offset,
        "round_trips": trips,
        "available_airlines": available_airlines,
    }
