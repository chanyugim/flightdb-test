from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.flight import SimpleAirport


class MemberResponse(BaseModel):
    member_id: str
    grade_code: str
    grade_name: str
    name: str
    birth_date: date
    gender: str
    phone: str
    point_balance: int
    role_type: str


class PointHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    point_history_id: int
    reservation_no: str
    change_type: str
    change_amount: int
    balance_after: int
    occurred_at: datetime


class MemberPointResponse(BaseModel):
    member_id: str
    point_balance: int
    history: list[PointHistoryItem]


class RouteRecommendation(BaseModel):
    departure_airport: SimpleAirport
    arrival_airport: SimpleAirport
    reservation_count: int
