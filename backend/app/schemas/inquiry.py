from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.validation import RequestModel


class InquiryCreate(RequestModel):
    reservation_no: str | None = Field(default=None, min_length=1, max_length=20)
    author_name: str = Field(min_length=1, max_length=30)
    author_phone: str = Field(min_length=1, max_length=20)
    inquiry_password: str | None = Field(default=None, min_length=4, max_length=100)
    subject: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=10000)


class InquiryReplyRequest(RequestModel):
    admin_reply: str = Field(min_length=1, max_length=10000)


class InquiryResponse(BaseModel):
    inquiry_id: int
    member_id: str | None
    reservation_no: str | None
    author_name: str
    author_phone: str
    subject: str
    content: str
    admin_reply: str | None
    reply_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuestInquiryLookupRequest(RequestModel):
    inquiry_id: int
    password: str = Field(min_length=1, max_length=100)
