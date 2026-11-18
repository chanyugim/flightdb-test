from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.models.member_account import MemberAccount
from app.models.member_grade import MemberGrade
from app.models.point_history import PointHistory
from app.models.reservation import Reservation
from app.services.route_stats import list_route_statistics


def get_recommended_routes(db: Session, limit: int, current_member: MemberAccount):
    return list_route_statistics(
        db, limit=limit, member_id=current_member.member_id, completed_only=True
    )


def get_me(db: Session, current_member: MemberAccount):
    grade = db.get(MemberGrade, current_member.grade_code)

    return member_to_dict(current_member, grade)


def get_my_points(db: Session, limit: int, offset: int, current_member: MemberAccount):
    stmt = (
        select(PointHistory)
        .join(
            Reservation,
            Reservation.reservation_no == PointHistory.reservation_no,
        )
        .where(Reservation.member_id == current_member.member_id)
        .order_by(PointHistory.occurred_at.desc(), PointHistory.point_history_id.desc())
        .offset(offset)
        .limit(limit)
    )

    history = db.scalars(stmt).all()

    return {
        "member_id": current_member.member_id,
        "point_balance": current_member.point_balance,
        "history": history,
    }


def get_my_inquiries(
    db: Session, limit: int, offset: int, current_member: MemberAccount
):
    stmt = (
        select(Inquiry)
        .where(Inquiry.member_id == current_member.member_id)
        .order_by(Inquiry.created_at.desc(), Inquiry.inquiry_id.desc())
        .offset(offset)
        .limit(limit)
    )
    return db.scalars(stmt).all()


def list_members(
    db: Session,
    keyword: str | None,
    role: Literal["일반", "관리자"] | None,
    limit: int,
    offset: int,
):
    stmt = select(MemberAccount, MemberGrade).join(
        MemberGrade, MemberGrade.grade_code == MemberAccount.grade_code
    )
    if keyword:
        search = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                MemberAccount.member_id.like(search),
                MemberAccount.name.like(search),
                MemberAccount.phone.like(search),
            )
        )
    if role:
        stmt = stmt.where(MemberAccount.role_type == role)
    rows = db.execute(
        stmt.order_by(MemberAccount.member_id).offset(offset).limit(limit)
    ).all()
    return [member_to_dict(member, grade) for member, grade in rows]


def get_member(db: Session, member_id: str):
    member = db.get(MemberAccount, member_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )
    grade = db.get(MemberGrade, member.grade_code)
    return member_to_dict(member, grade)


def member_to_dict(member, grade):
    return {
        "member_id": member.member_id,
        "grade_code": member.grade_code,
        "grade_name": grade.grade_name if grade else member.grade_code,
        "name": member.name,
        "birth_date": member.birth_date,
        "gender": member.gender,
        "phone": member.phone,
        "point_balance": member.point_balance,
        "role_type": member.role_type,
    }
