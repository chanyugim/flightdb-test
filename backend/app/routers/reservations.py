from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    get_current_member,
    get_optional_current_member,
)
from app.core.rate_limit import limit_sensitive_requests
from app.models.member_account import MemberAccount
from app.schemas.common import MessageResponse
from app.schemas.reservation import (
    GuestReservationLookupRequest,
    ReservationCreate,
    ReservationCreatedResponse,
    ReservationResponse,
    RoundTripReservationCreate,
)
from app.services import reservations as reservations_service

router = APIRouter(prefix="/reservations", tags=["reservations"])

IdempotencyKey = Annotated[
    str | None,
    Header(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$"),
]


@router.post(
    "",
    response_model=ReservationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation(
    payload: ReservationCreate,
    current_member: MemberAccount | None = Depends(get_optional_current_member),
    db: Session = Depends(get_db),
    idempotency_key: IdempotencyKey = None,
):
    return reservations_service.create_reservation(
        payload=payload,
        current_member=current_member,
        db=db,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/round-trip",
    response_model=ReservationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_round_trip_reservation(
    payload: RoundTripReservationCreate,
    current_member: MemberAccount | None = Depends(get_optional_current_member),
    db: Session = Depends(get_db),
    idempotency_key: IdempotencyKey = None,
):
    return reservations_service.create_reservation(
        payload=payload,
        current_member=current_member,
        db=db,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/guest/lookup",
    dependencies=[Depends(limit_sensitive_requests)],
    response_model=ReservationResponse,
)
def guest_lookup(
    payload: GuestReservationLookupRequest,
    db: Session = Depends(get_db),
):
    return reservations_service.guest_lookup(payload=payload, db=db)


@router.post(
    "/guest/cancel",
    dependencies=[Depends(limit_sensitive_requests)],
    response_model=MessageResponse,
)
def guest_cancel(
    payload: GuestReservationLookupRequest,
    db: Session = Depends(get_db),
):
    return reservations_service.guest_cancel(payload=payload, db=db)


@router.get(
    "/{reservation_no}",
    response_model=ReservationResponse,
)
def get_reservation(
    reservation_no: str,
    current_member: MemberAccount = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    return reservations_service.get_reservation(
        reservation_no=reservation_no, current_member=current_member, db=db
    )


@router.post(
    "/{reservation_no}/cancel",
    response_model=MessageResponse,
)
def cancel_reservation(
    reservation_no: str,
    current_member: MemberAccount = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    return reservations_service.cancel_reservation(
        reservation_no=reservation_no, current_member=current_member, db=db
    )
