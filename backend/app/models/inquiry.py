from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Inquiry(Base):
    __tablename__ = "inquiry"
    __table_args__ = (
        CheckConstraint(
            "reply_status IN ('답변대기', '답변완료')", name="ck_inquiry_reply"
        ),
        ForeignKeyConstraint(
            ["member_id"],
            ["member_account.member_id"],
            name="fk_inquiry_member",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["reservation_no"],
            ["reservation.reservation_no"],
            name="fk_inquiry_reservation",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        Index("idx_inquiry_member_date", "member_id", "created_at"),
    )

    inquiry_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[str | None] = mapped_column(String(20))
    reservation_no: Mapped[str | None] = mapped_column(String(20))
    author_name: Mapped[str] = mapped_column(String(30), nullable=False)
    author_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    inquiry_password: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    admin_reply: Mapped[str | None] = mapped_column(Text)
    reply_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'답변대기'")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
