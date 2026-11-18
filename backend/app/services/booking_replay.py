import base64
import hashlib

from fastapi import HTTPException
from sqlalchemy import func, select

from app.models.point_history import PointHistory
from app.models.reservation import Reservation
from app.models.reservation_detail import ReservationDetail
from app.models.seat import Seat


def reservation_number(key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return "I" + base64.b32encode(digest).decode("ascii")[:19]


def find_replay(db, reservation_no, payload, member, passengers, is_round_trip):
    if reservation_no is None:
        return None
    reservation = db.scalar(
        select(Reservation)
        .where(Reservation.reservation_no == reservation_no)
        .execution_options(populate_existing=True)
    )
    if reservation is None:
        return None

    details = db.execute(
        select(ReservationDetail, Seat.flight_id)
        .join(Seat, Seat.seat_id == ReservationDetail.seat_id)
        .where(ReservationDetail.reservation_no == reservation_no)
        .order_by(ReservationDetail.reservation_detail_id)
    ).all()
    same_contact = all(
        getattr(reservation, name) == value
        for name, value in payload.model_dump(exclude={"passengers"}).items()
    )
    saved_passengers = [
        (detail.seat_id, detail.passenger_name, detail.passenger_birth_date)
        for detail, _ in details
    ]
    requested_passengers = [
        (p.seat_id, p.passenger_name, p.passenger_birth_date) for p in passengers
    ]
    if (
        reservation.member_id != (member.member_id if member else None)
        or not same_contact
        or saved_passengers != requested_passengers
        or len({flight_id for _, flight_id in details}) != (2 if is_round_trip else 1)
    ):
        raise HTTPException(
            409, "Idempotency-Key was already used for a different request"
        )

    earned_points = db.scalar(
        select(func.coalesce(func.sum(PointHistory.change_amount), 0)).where(
            PointHistory.reservation_no == reservation_no,
            PointHistory.change_type == "적립",
        )
    )
    return {
        "reservation_no": reservation_no,
        "final_amount": reservation.final_amount,
        "earned_points": earned_points,
        "reservation_status": reservation.reservation_status,
        "trip_type": "round_trip" if is_round_trip else "one_way",
        "idempotent_replay": True,
    }
