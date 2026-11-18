from decimal import Decimal

from sqlalchemy import CheckConstraint, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MemberGrade(Base):
    __tablename__ = "member_grade"
    __table_args__ = (
        CheckConstraint("upgrade_requirement >= 0", name="ck_grade_requirement"),
        CheckConstraint("point_rate BETWEEN 0 AND 100", name="ck_grade_point_rate"),
    )

    grade_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    grade_name: Mapped[str] = mapped_column(String(20), nullable=False)
    upgrade_requirement: Mapped[int] = mapped_column(Integer, nullable=False)
    point_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
