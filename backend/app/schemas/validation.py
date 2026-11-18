from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, field_validator

from app.core.time import local_datetime, now_local


def valid_birth_date(value: date) -> date:
    if value > now_local().date():
        raise ValueError("Birth date cannot be in the future")
    return value


BirthDate = Annotated[date, AfterValidator(valid_birth_date)]
BusinessDateTime = Annotated[datetime, AfterValidator(local_datetime)]


class RequestModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def trim_text(cls, value, info):
        # 비밀번호의 공백은 입력값의 일부이므로 변경하지 않음.
        if isinstance(value, str) and info.field_name not in {
            "password",
            "inquiry_password",
        }:
            return value.strip()
        return value
