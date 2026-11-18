from datetime import date

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MemberAccount(Base):
    __tablename__ = "member_account"
    __table_args__ = (
        CheckConstraint("point_balance >= 0", name="ck_member_points"),
        CheckConstraint("role_type IN ('일반', '관리자')", name="ck_member_role"),
        ForeignKeyConstraint(
            ["grade_code"],
            ["member_grade.grade_code"],
            name="fk_member_grade",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
    )

    member_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    grade_code: Mapped[str] = mapped_column(String(10), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    point_balance: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    role_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'일반'")
    )
