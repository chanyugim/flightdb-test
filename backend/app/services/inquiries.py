from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.schemas.inquiry import InquiryReplyRequest


def list_inquiries(
    db: Session,
    reply_status: Literal["답변대기", "답변완료"] | None,
    limit: int,
    offset: int,
):
    stmt = select(Inquiry)
    if reply_status:
        stmt = stmt.where(Inquiry.reply_status == reply_status)
    return db.scalars(
        stmt.order_by(Inquiry.created_at.desc()).offset(offset).limit(limit)
    ).all()


def get_inquiry(db: Session, inquiry_id: int):
    inquiry = db.get(Inquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found"
        )
    return inquiry


def reply_inquiry(db: Session, inquiry_id: int, payload: InquiryReplyRequest):
    inquiry = db.get(Inquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found"
        )
    inquiry.admin_reply = payload.admin_reply
    inquiry.reply_status = "답변완료"
    db.commit()
    db.refresh(inquiry)
    return inquiry
