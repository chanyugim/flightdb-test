from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_member
from app.models.member_account import MemberAccount
from app.schemas.inquiry import InquiryResponse
from app.schemas.member import MemberPointResponse, MemberResponse, RouteRecommendation
from app.schemas.reservation import ReservationResponse
from app.services import members as members_service
from app.services import reservations as reservations_service

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/recommended-routes", response_model=list[RouteRecommendation])
def get_recommended_routes(
    limit: int = Query(default=5, ge=1, le=20),
    current_member: MemberAccount = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    return members_service.get_recommended_routes(
        limit=limit, current_member=current_member, db=db
    )


@router.get("", response_model=MemberResponse)
def get_me(
    current_member: MemberAccount = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    return members_service.get_me(current_member=current_member, db=db)


@router.get("/points", response_model=MemberPointResponse)
def get_my_points(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_member: MemberAccount = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    return members_service.get_my_points(
        limit=limit, offset=offset, current_member=current_member, db=db
    )


@router.get("/reservations", response_model=list[ReservationResponse])
def get_my_reservations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_member: MemberAccount = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    return reservations_service.get_my_reservations(
        limit=limit, offset=offset, current_member=current_member, db=db
    )


@router.get("/inquiries", response_model=list[InquiryResponse])
def get_my_inquiries(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_member: MemberAccount = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    return members_service.get_my_inquiries(
        limit=limit, offset=offset, current_member=current_member, db=db
    )
