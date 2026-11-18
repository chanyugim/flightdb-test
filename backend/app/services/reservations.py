import secrets
from collections import Counter
from decimal import ROUND_DOWN, Decimal
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.core.time import now_local
from app.models.airline import Airline
from app.models.airport import Airport
from app.models.flight import Flight
from app.models.member_account import MemberAccount
from app.models.member_grade import MemberGrade
from app.models.point_history import PointHistory
from app.models.promotion import Promotion
from app.models.reservation import Reservation
from app.models.reservation_detail import ReservationDetail
from app.models.seat import Seat
from app.schemas.reservation import (
    GuestReservationLookupRequest,
    PassengerCreate,
    ReservationCreate,
    RoundTripReservationCreate,
)
from app.services.booking_replay import find_replay, reservation_number
from app.services.flights import flight_to_dict


def reservation_responses(db: Session, reservations: list[Reservation]) -> list[dict]:
    """목록의 예약 상세와 항공편을 한 번에 조회함."""
    if not reservations:
        return []
    departure, arrival = aliased(Airport), aliased(Airport)
    rows = db.execute(
        select(ReservationDetail, Seat, Flight, Airline, departure, arrival)
        .join(Seat, Seat.seat_id == ReservationDetail.seat_id)
        .join(Flight, Flight.flight_id == Seat.flight_id)
        .join(Airline, Airline.airline_id == Flight.airline_id)
        .join(departure, departure.airport_id == Flight.departure_airport_id)
        .join(arrival, arrival.airport_id == Flight.arrival_airport_id)
        .where(
            ReservationDetail.reservation_no.in_(
                [r.reservation_no for r in reservations]
            )
        )
        # 출국 좌석을 먼저 저장하므로 운항 시각 변경 후에도 구간 순서를 유지함.
        .order_by(ReservationDetail.reservation_detail_id)
    ).all()
    grouped = {}
    segment_map = {}
    for detail, seat, flight, airline, dep, arr in rows:
        entry = grouped.setdefault(
            detail.reservation_no,
            {
                "flight": None,
                "details": [],
                "segments": [],
            },
        )
        item = {
            "reservation_detail_id": detail.reservation_detail_id,
            "seat_id": seat.seat_id,
            "flight_id": flight.flight_id,
            "seat_no": seat.seat_no,
            "seat_class": seat.seat_class,
            "passenger_name": detail.passenger_name,
            "passenger_birth_date": detail.passenger_birth_date,
        }
        entry["details"].append(item)
        key = (detail.reservation_no, flight.flight_id)
        segment = segment_map.get(key)
        if segment is None:
            segment = {
                "direction": "outbound" if not entry["segments"] else "inbound",
                "flight": flight_to_dict(flight, airline, dep, arr),
                "details": [],
            }
            entry["segments"].append(segment)
            segment_map[key] = segment
            if entry["flight"] is None:
                entry["flight"] = segment["flight"]
        segment["details"].append(item)
    result = []
    for reservation in reservations:
        data = {
            column.name: getattr(reservation, column.name)
            for column in Reservation.__table__.columns
        }
        data.update(
            grouped.get(
                reservation.reservation_no,
                {"flight": None, "details": [], "segments": []},
            )
        )
        data["trip_type"] = "round_trip" if len(data["segments"]) == 2 else "one_way"
        result.append(data)
    return result


def build_reservation_response(db: Session, reservation_no: str) -> dict:
    reservation = db.get(Reservation, reservation_no)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation_responses(db, [reservation])[0]


def _new_reservation_no() -> str:
    return (
        "R" + now_local().strftime("%Y%m%d%H%M%S") + f"{secrets.randbelow(100000):05d}"
    )


def _verify_guest_reservation(
    db: Session,
    payload: GuestReservationLookupRequest,
) -> Reservation:
    reservation = db.get(Reservation, payload.reservation_no)

    if (
        reservation is None
        or reservation.member_id is not None
        or reservation.booker_email != payload.booker_email
        or reservation.booker_phone != payload.booker_phone
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest reservation not found",
        )

    return reservation


def _cancel_locked_reservation(
    db: Session,
    reservation: Reservation,
) -> None:
    if reservation.reservation_status == "취소":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reservation is already cancelled",
        )

    details = db.scalars(
        select(ReservationDetail)
        .where(ReservationDetail.reservation_no == reservation.reservation_no)
        .order_by(ReservationDetail.seat_id)
    ).all()

    seat_ids = [detail.seat_id for detail in details]

    if not seat_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reservation has no seat details",
        )

    seats = db.scalars(
        select(Seat)
        .where(Seat.seat_id.in_(seat_ids))
        .order_by(Seat.seat_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()

    flight_ids = {seat.flight_id for seat in seats}

    if not 1 <= len(flight_ids) <= 2:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid reservation seat state",
        )

    flights = db.scalars(
        select(Flight)
        .where(Flight.flight_id.in_(flight_ids))
        .order_by(Flight.flight_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()

    if len(flights) != len(flight_ids):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Flight data is inconsistent",
        )

    if any(
        flight.flight_status == "완료"
        or (flight.flight_status != "결항" and flight.departure_at <= now_local())
        for flight in flights
    ):
        raise HTTPException(
            status_code=409, detail="Departed flights cannot be cancelled"
        )
    if len(seats) != len(seat_ids) or any(seat.is_available for seat in seats):
        raise HTTPException(
            status_code=409, detail="Reservation seat data is inconsistent"
        )

    for seat in seats:
        seat.is_available = True

    seat_counts = Counter(seat.flight_id for seat in seats)
    for flight in flights:
        flight.remaining_seats += seat_counts[flight.flight_id]

    if reservation.member_id:
        _reverse_reservation_points(db, reservation)

    reservation.reservation_status = "취소"


def _booking_passengers(payload):
    is_round_trip = isinstance(payload, RoundTripReservationCreate)
    if is_round_trip:
        passengers = [
            PassengerCreate(
                seat_id=seat_id,
                passenger_name=p.passenger_name,
                passenger_birth_date=p.passenger_birth_date,
            )
            for p in payload.passengers
            for seat_id in (p.outbound_seat_id, p.inbound_seat_id)
        ]
    else:
        passengers = payload.passengers
    seat_ids = [p.seat_id for p in passengers]

    if len(set(seat_ids)) != len(seat_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate seat_id in passengers",
        )

    return passengers, seat_ids, is_round_trip


def _lock_booking_seats(db, seat_ids):
    seats = db.scalars(
        select(Seat)
        .where(Seat.seat_id.in_(seat_ids))
        .order_by(Seat.seat_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()

    if len(seats) != len(seat_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more seats do not exist",
        )

    return seats


def _lock_booking_flights(db, seats, is_round_trip):
    flight_ids = {seat.flight_id for seat in seats}

    if len(flight_ids) != (2 if is_round_trip else 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seats must belong to exactly two flights for round trips or one flight for one-way bookings",
        )

    flights = db.scalars(
        select(Flight)
        .where(Flight.flight_id.in_(flight_ids))
        .order_by(Flight.flight_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()

    if len(flights) != len(flight_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found",
        )

    if any(
        flight.flight_status in {"결항", "완료"} or flight.departure_at <= now_local()
        for flight in flights
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This flight cannot be reserved",
        )

    return flights


def _validate_round_trip(payload, seat_map, flight_map):
    outbound_ids = {seat_map[p.outbound_seat_id].flight_id for p in payload.passengers}
    inbound_ids = {seat_map[p.inbound_seat_id].flight_id for p in payload.passengers}
    if len(outbound_ids) != 1 or len(inbound_ids) != 1 or outbound_ids == inbound_ids:
        raise HTTPException(
            400,
            "All passengers must travel on the same outbound and inbound flights",
        )
    outbound = flight_map[next(iter(outbound_ids))]
    inbound = flight_map[next(iter(inbound_ids))]
    if (
        outbound.departure_airport_id != inbound.arrival_airport_id
        or outbound.arrival_airport_id != inbound.departure_airport_id
        or outbound.arrival_at >= inbound.departure_at
    ):
        raise HTTPException(400, "Invalid round-trip route or return time")


def _lock_booking_member(db, current_member, used_points):
    member = None
    grade = None

    if current_member is not None:
        member = db.scalar(
            select(MemberAccount)
            .where(MemberAccount.member_id == current_member.member_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if member is None:
            raise HTTPException(409, "Member data is inconsistent")
        grade = db.get(MemberGrade, member.grade_code)

        if used_points > member.point_balance:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Insufficient points",
            )
    elif used_points > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guest reservations cannot use points",
        )

    return member, grade


def _booking_amount(db, promotion_id, used_points, subtotal):
    promotion = None
    discount_amount = 0

    if promotion_id is not None:
        promotion = db.get(
            Promotion,
            promotion_id,
        )

        if promotion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found",
            )

        now = now_local()
        if not (promotion.start_at <= now <= promotion.end_at):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Promotion is not active",
            )

    if promotion:
        discount_amount = int(
            (Decimal(subtotal) * promotion.discount_rate / Decimal("100")).quantize(
                Decimal("1"),
                rounding=ROUND_DOWN,
            )
        )

    final_amount = subtotal - discount_amount - used_points

    if final_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Used points exceed payable amount",
        )

    return final_amount


def _insert_reservation(db, payload, member, final_amount, reservation_no=None):
    if reservation_no is None:
        reservation_no = _new_reservation_no()
        while db.get(Reservation, reservation_no) is not None:
            reservation_no = _new_reservation_no()

    reservation = Reservation(
        reservation_no=reservation_no,
        member_id=(member.member_id if member is not None else None),
        promotion_id=payload.promotion_id,
        booker_name=payload.booker_name,
        booker_phone=payload.booker_phone,
        booker_email=payload.booker_email,
        booker_birth_date=payload.booker_birth_date,
        used_points=payload.used_points,
        final_amount=final_amount,
        reserved_at=now_local(),
        reservation_status="확정",
    )
    db.add(reservation)
    db.flush()

    return reservation_no


def _reserve_seats(db, reservation_no, passengers, seat_map, seats, flights):
    for passenger in passengers:
        db.add(
            ReservationDetail(
                reservation_no=reservation_no,
                seat_id=passenger.seat_id,
                passenger_name=passenger.passenger_name,
                passenger_birth_date=(passenger.passenger_birth_date),
            )
        )
        seat_map[passenger.seat_id].is_available = False

    seat_counts = Counter(seat.flight_id for seat in seats)
    for flight in flights:
        flight.remaining_seats -= seat_counts[flight.flight_id]
        if flight.remaining_seats < 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Not enough remaining seats",
            )


def _apply_booking_points(db, member, grade, used_points, final_amount, reservation_no):
    earned_points = 0

    if member:
        balance = member.point_balance

        if used_points > 0:
            balance -= used_points
            member.point_balance = balance
            db.add(
                PointHistory(
                    reservation_no=reservation_no,
                    change_type="사용",
                    change_amount=used_points,
                    balance_after=balance,
                    occurred_at=now_local(),
                )
            )

        if grade:
            earned_points = int(
                (Decimal(final_amount) * grade.point_rate / Decimal("100")).quantize(
                    Decimal("1"),
                    rounding=ROUND_DOWN,
                )
            )

        if earned_points > 0:
            balance += earned_points
            member.point_balance = balance
            db.add(
                PointHistory(
                    reservation_no=reservation_no,
                    change_type="적립",
                    change_amount=earned_points,
                    balance_after=balance,
                    occurred_at=now_local(),
                )
            )

    return earned_points


def create_reservation(
    db: Session,
    payload: ReservationCreate | RoundTripReservationCreate,
    current_member: MemberAccount | None,
    idempotency_key: str | None = None,
):
    passengers, seat_ids, is_round_trip = _booking_passengers(payload)
    number = reservation_number(idempotency_key) if idempotency_key else None

    def replay():
        return find_replay(
            db, number, payload, current_member, passengers, is_round_trip
        )

    try:
        previous = replay()
        if previous is not None:
            db.rollback()
            return previous
        if current_member is None and payload.promotion_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="프로모션 할인은 로그인한 회원만 이용할 수 있어요.",
            )
        seats = _lock_booking_seats(db, seat_ids)
        # 같은 좌석의 잠금을 기다린 재전송은 먼저 완료된 예약을 다시 확인함.
        previous = replay()
        if previous is not None:
            db.rollback()
            return previous
        if any(not seat.is_available for seat in seats):
            raise HTTPException(409, "One or more seats are already reserved")
        flights = _lock_booking_flights(db, seats, is_round_trip)
        seat_map = {seat.seat_id: seat for seat in seats}
        flight_map = {flight.flight_id: flight for flight in flights}
        if is_round_trip:
            _validate_round_trip(payload, seat_map, flight_map)
        member, grade = _lock_booking_member(db, current_member, payload.used_points)
        subtotal = sum(flight_map[seat.flight_id].base_price for seat in seats)
        final_amount = _booking_amount(
            db, payload.promotion_id, payload.used_points, subtotal
        )
        reservation_no = _insert_reservation(db, payload, member, final_amount, number)
        _reserve_seats(db, reservation_no, passengers, seat_map, seats, flights)
        earned_points = _apply_booking_points(
            db, member, grade, payload.used_points, final_amount, reservation_no
        )
        db.commit()
        return {
            "reservation_no": reservation_no,
            "final_amount": final_amount,
            "earned_points": earned_points,
            "reservation_status": "확정",
            "trip_type": "round_trip" if is_round_trip else "one_way",
        }
    except IntegrityError:
        db.rollback()
        try:
            previous = replay()
        finally:
            db.rollback()
        if previous is not None:
            return previous
        raise
    except Exception:
        db.rollback()
        raise


def guest_lookup(db: Session, payload: GuestReservationLookupRequest):
    reservation = _verify_guest_reservation(db, payload)
    return build_reservation_response(
        db,
        reservation.reservation_no,
    )


def guest_cancel(db: Session, payload: GuestReservationLookupRequest):
    try:
        reservation = db.scalar(
            select(Reservation)
            .where(Reservation.reservation_no == payload.reservation_no)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        if (
            reservation is None
            or reservation.member_id is not None
            or reservation.booker_email != payload.booker_email
            or reservation.booker_phone != payload.booker_phone
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest reservation not found",
            )

        _cancel_locked_reservation(db, reservation)
        db.commit()

        return {
            "message": "Reservation cancelled",
        }
    except Exception:
        db.rollback()
        raise


def get_reservation(db: Session, reservation_no: str, current_member: MemberAccount):
    reservation = db.get(Reservation, reservation_no)

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    if (
        current_member.role_type != "관리자"
        and reservation.member_id != current_member.member_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this reservation",
        )

    return build_reservation_response(
        db,
        reservation_no,
    )


def cancel_reservation(db: Session, reservation_no: str, current_member: MemberAccount):
    try:
        reservation = db.scalar(
            select(Reservation)
            .where(Reservation.reservation_no == reservation_no)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found",
            )

        if (
            current_member.role_type != "관리자"
            and reservation.member_id != current_member.member_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot cancel this reservation",
            )

        _cancel_locked_reservation(db, reservation)
        db.commit()

        return {
            "message": "Reservation cancelled",
        }

    except Exception:
        db.rollback()
        raise


def get_my_reservations(
    db: Session, limit: int, offset: int, current_member: MemberAccount
):
    reservations = db.scalars(
        select(Reservation)
        .where(Reservation.member_id == current_member.member_id)
        .order_by(Reservation.reserved_at.desc(), Reservation.reservation_no)
        .offset(offset)
        .limit(limit)
    ).all()

    return reservation_responses(db, reservations)


def list_admin_reservations(
    db: Session,
    member_id: str | None,
    reservation_status: Literal["확정", "취소"] | None,
    keyword: str | None,
    limit: int,
    offset: int,
):
    stmt = select(Reservation)
    if member_id is not None:
        stmt = stmt.where(Reservation.member_id == member_id)
    if reservation_status is not None:
        stmt = stmt.where(Reservation.reservation_status == reservation_status)
    if keyword and keyword.strip():
        stmt = stmt.where(
            or_(
                Reservation.reservation_no.contains(keyword.strip(), autoescape=True),
                Reservation.booker_name.contains(keyword.strip(), autoescape=True),
                Reservation.booker_phone.contains(keyword.strip(), autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    reservations = db.scalars(
        stmt.order_by(Reservation.reserved_at.desc(), Reservation.reservation_no)
        .offset(offset)
        .limit(limit)
    ).all()
    return {
        "count": len(reservations),
        "total": total,
        "offset": offset,
        "limit": limit,
        "reservations": reservation_responses(db, reservations),
    }


def _reverse_reservation_points(db, reservation):
    member = db.scalar(
        select(MemberAccount)
        .where(MemberAccount.member_id == reservation.member_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member data is inconsistent",
        )

    balance = member.point_balance

    if reservation.used_points > 0:
        balance += reservation.used_points
        member.point_balance = balance
        db.add(
            PointHistory(
                reservation_no=reservation.reservation_no,
                change_type="반환",
                change_amount=reservation.used_points,
                balance_after=balance,
                occurred_at=now_local(),
            )
        )

    earned_points, already_reclaimed = db.execute(
        select(
            *[
                func.coalesce(
                    func.sum(
                        case(
                            (
                                PointHistory.change_type == change_type,
                                PointHistory.change_amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                )
                for change_type in ("적립", "회수")
            ]
        ).where(PointHistory.reservation_no == reservation.reservation_no)
    ).one()

    reclaim_amount = max(
        int(earned_points) - int(already_reclaimed),
        0,
    )

    if reclaim_amount > 0:
        if balance < reclaim_amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=("Insufficient point balance to reclaim earned points"),
            )

        balance -= reclaim_amount
        member.point_balance = balance
        db.add(
            PointHistory(
                reservation_no=reservation.reservation_no,
                change_type="회수",
                change_amount=reclaim_amount,
                balance_after=balance,
                occurred_at=now_local(),
            )
        )
