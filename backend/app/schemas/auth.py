from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.validation import BirthDate, RequestModel


class RegisterRequest(RequestModel):
    member_id: str = Field(min_length=4, max_length=20)
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=30)
    birth_date: BirthDate
    gender: Literal["M", "F"]
    phone: str = Field(min_length=1, max_length=20)

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class LoginRequest(RequestModel):
    member_id: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
