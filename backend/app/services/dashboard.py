from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.flight import Flight
from app.models.inquiry import Inquiry
from app.models.member_account import MemberAccount
from app.models.reservation import Reservation


def get_summary(db: Session):
    stmt = select(
        select(func.count())
        .select_from(MemberAccount)
        .scalar_subquery()
        .label("members"),
        select(func.count()).select_from(Flight).scalar_subquery().label("flights"),
        select(func.count())
        .select_from(Reservation)
        .where(Reservation.reservation_status == "확정")
        .scalar_subquery()
        .label("confirmed_reservations"),
        select(func.count())
        .select_from(Inquiry)
        .where(Inquiry.reply_status == "답변대기")
        .scalar_subquery()
        .label("pending_inquiries"),
    )
    return dict(db.execute(stmt).mappings().one())
