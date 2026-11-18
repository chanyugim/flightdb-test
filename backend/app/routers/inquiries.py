from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_optional_current_member
from app.core.rate_limit import limit_sensitive_requests
from app.core.security import hash_password, verify_password_or_dummy
from app.core.time import now_local
from app.models.inquiry import Inquiry
from app.models.member_account import MemberAccount
from app.models.reservation import Reservation
from app.schemas.inquiry import (
    GuestInquiryLookupRequest,
    InquiryCreate,
    InquiryResponse,
)

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(
    payload: InquiryCreate,
    current_member: MemberAccount | None = Depends(get_optional_current_member),
    db: Session = Depends(get_db),
):
    member_id = current_member.member_id if current_member else None
    if payload.reservation_no:
        reservation = db.get(Reservation, payload.reservation_no)
        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )
        if (
            current_member is not None
            and current_member.role_type != "관리자"
            and reservation.member_id != current_member.member_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot attach this reservation",
            )
        if current_member is None and reservation.member_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Guest cannot attach a member reservation",
            )
        if current_member is None and reservation.booker_phone != payload.author_phone:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reservation phone does not match",
            )
    if current_member is None:
        if not payload.inquiry_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guest inquiry requires inquiry_password",
            )
        password_value = hash_password(payload.inquiry_password)
    else:
        password_value = None
    inquiry = Inquiry(
        member_id=member_id,
        reservation_no=payload.reservation_no,
        author_name=payload.author_name,
        author_phone=payload.author_phone,
        inquiry_password=password_value,
        subject=payload.subject,
        content=payload.content,
        admin_reply=None,
        reply_status="답변대기",
        created_at=now_local(),
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return inquiry


@router.post(
    "/guest/lookup",
    response_model=InquiryResponse,
    dependencies=[Depends(limit_sensitive_requests)],
)
def guest_inquiry_lookup(
    payload: GuestInquiryLookupRequest, db: Session = Depends(get_db)
):
    inquiry = db.get(Inquiry, payload.inquiry_id)
    password_ok = verify_password_or_dummy(
        payload.password,
        inquiry.inquiry_password
        if inquiry is not None and inquiry.member_id is None
        else None,
    )
    if (
        inquiry is None
        or inquiry.member_id is not None
        or not inquiry.inquiry_password
        or not password_ok
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Guest inquiry not found"
        )
    return inquiry
