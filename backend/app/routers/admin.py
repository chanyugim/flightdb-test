from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.member_account import MemberAccount
from app.schemas.admin import (
    AdminSummaryResponse,
    FlightCreateRequest,
    FlightStatus,
    FlightUpdateRequest,
    PromotionCreateRequest,
    PromotionUpdateRequest,
    SeatBulkCreateRequest,
)
from app.schemas.flight import FlightListResponse, FlightResponse
from app.schemas.inquiry import InquiryReplyRequest, InquiryResponse
from app.schemas.member import MemberResponse
from app.schemas.promotion import PromotionResponse
from app.schemas.reservation import ReservationListResponse
from app.schemas.seat import SeatListResponse
from app.services import dashboard as dashboard_service
from app.services import flights as flights_service
from app.services import inquiries as inquiries_service
from app.services import members as members_service
from app.services import promotions as promotions_service
from app.services import reservations as reservations_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/reservations", response_model=ReservationListResponse)
def get_reservations(
    member_id: str | None = Query(default=None, max_length=20),
    reservation_status: Literal["확정", "취소"] | None = Query(
        default=None, alias="status"
    ),
    keyword: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return reservations_service.list_admin_reservations(
        member_id=member_id,
        reservation_status=reservation_status,
        keyword=keyword,
        limit=limit,
        offset=offset,
        db=db,
    )


@router.get("/summary", response_model=AdminSummaryResponse)
def get_summary(
    _: MemberAccount = Depends(require_admin), db: Session = Depends(get_db)
):
    return dashboard_service.get_summary(db=db)


@router.get("/members", response_model=list[MemberResponse])
def get_members(
    keyword: str | None = Query(default=None, max_length=50),
    role: Literal["일반", "관리자"] | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return members_service.list_members(
        keyword=keyword, role=role, limit=limit, offset=offset, db=db
    )


@router.get("/members/{member_id}", response_model=MemberResponse)
def get_member(
    member_id: str,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return members_service.get_member(member_id=member_id, db=db)


@router.get("/flights", response_model=FlightListResponse)
def get_flights(
    flight_status: FlightStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return flights_service.list_admin_flights(
        flight_status=flight_status, limit=limit, offset=offset, db=db
    )


@router.post(
    "/flights", response_model=FlightResponse, status_code=status.HTTP_201_CREATED
)
def create_flight(
    payload: FlightCreateRequest,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return flights_service.create_flight(payload=payload, db=db)


@router.patch("/flights/{flight_id}", response_model=FlightResponse)
def update_flight(
    flight_id: int,
    payload: FlightUpdateRequest,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return flights_service.update_flight(flight_id=flight_id, payload=payload, db=db)


@router.get("/flights/{flight_id}/seats", response_model=SeatListResponse)
def get_flight_seats(
    flight_id: int,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return flights_service.list_admin_flight_seats(flight_id=flight_id, db=db)


@router.post(
    "/flights/{flight_id}/seats",
    response_model=SeatListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_flight_seats(
    flight_id: int,
    payload: SeatBulkCreateRequest,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return flights_service.create_flight_seats(
        flight_id=flight_id, payload=payload, db=db
    )


@router.get("/promotions", response_model=list[PromotionResponse])
def get_promotions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return promotions_service.list_admin_promotions(limit=limit, offset=offset, db=db)


@router.post(
    "/promotions", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED
)
def create_promotion(
    payload: PromotionCreateRequest,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return promotions_service.create_promotion(payload=payload, db=db)


@router.patch("/promotions/{promotion_id}", response_model=PromotionResponse)
def update_promotion(
    promotion_id: int,
    payload: PromotionUpdateRequest,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return promotions_service.update_promotion(
        promotion_id=promotion_id, payload=payload, db=db
    )


@router.delete("/promotions/{promotion_id}")
def delete_promotion(
    promotion_id: int,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return promotions_service.delete_promotion(promotion_id=promotion_id, db=db)


@router.get("/inquiries", response_model=list[InquiryResponse])
def get_inquiries(
    reply_status: Literal["답변대기", "답변완료"] | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return inquiries_service.list_inquiries(
        reply_status=reply_status, limit=limit, offset=offset, db=db
    )


@router.get("/inquiries/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry(
    inquiry_id: int,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return inquiries_service.get_inquiry(inquiry_id=inquiry_id, db=db)


@router.patch("/inquiries/{inquiry_id}/reply", response_model=InquiryResponse)
def reply_inquiry(
    inquiry_id: int,
    payload: InquiryReplyRequest,
    _: MemberAccount = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return inquiries_service.reply_inquiry(
        inquiry_id=inquiry_id, payload=payload, db=db
    )
