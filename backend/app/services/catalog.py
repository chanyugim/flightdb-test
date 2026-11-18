from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import now_local
from app.models.member_grade import MemberGrade
from app.models.promotion import Promotion


def list_grades(db: Session):
    return db.scalars(
        select(MemberGrade).order_by(
            MemberGrade.upgrade_requirement, MemberGrade.grade_code
        )
    ).all()


def list_promotions(
    db: Session, *, active_only=True, limit=None, offset=0, ending_first=False
):
    stmt = select(Promotion)
    if active_only:
        current = now_local()
        stmt = stmt.where(Promotion.start_at <= current, Promotion.end_at >= current)
    ordering = Promotion.end_at if ending_first else Promotion.start_at.desc()
    return db.scalars(
        stmt.order_by(ordering, Promotion.promotion_id).offset(offset).limit(limit)
    ).all()
