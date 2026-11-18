from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.core.time import now_local
from app.models.airport import Airport
from app.models.flight import Flight
from app.models.reservation import Reservation
from app.models.reservation_detail import ReservationDetail
from app.models.seat import Seat
from app.schemas.flight import SimpleAirport


def list_route_statistics(
    db, *, limit, member_id=None, days=None, completed_only=False, current_month=False
):
    current = now_local()
    stmt = (
        select(
            Flight.departure_airport_id,
            Flight.arrival_airport_id,
            func.count(func.distinct(Reservation.reservation_no)).label("bookings"),
        )
        .select_from(Reservation)
        .join(
            ReservationDetail,
            ReservationDetail.reservation_no == Reservation.reservation_no,
        )
        .join(Seat, Seat.seat_id == ReservationDetail.seat_id)
        .join(Flight, Flight.flight_id == Seat.flight_id)
        .where(
            Reservation.reservation_status == "확정",
            Flight.flight_status != "결항",
            Reservation.reserved_at <= current,
        )
    )
    if member_id is not None:
        stmt = stmt.where(Reservation.member_id == member_id)
    if current_month:
        month_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt = stmt.where(Reservation.reserved_at >= month_start)
    elif days is not None:
        stmt = stmt.where(Reservation.reserved_at >= current - timedelta(days=days))
    if completed_only:
        stmt = stmt.where(Flight.arrival_at <= current)
    # 동행자 수와 관계없이 같은 예약의 같은 방향 노선은 한 건으로 집계함.
    routes = stmt.group_by(
        Flight.departure_airport_id, Flight.arrival_airport_id
    ).subquery()
    departure, arrival = aliased(Airport), aliased(Airport)
    rows = db.execute(
        select(departure, arrival, routes.c.bookings)
        .select_from(routes)
        .join(departure, departure.airport_id == routes.c.departure_airport_id)
        .join(arrival, arrival.airport_id == routes.c.arrival_airport_id)
        .order_by(routes.c.bookings.desc(), departure.airport_id, arrival.airport_id)
        .limit(limit)
    ).all()
    return [
        {
            "departure_airport": SimpleAirport.model_validate(
                dep, from_attributes=True
            ),
            "arrival_airport": SimpleAirport.model_validate(arr, from_attributes=True),
            "reservation_count": count,
        }
        for dep, arr, count in rows
    ]
