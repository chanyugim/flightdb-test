from datetime import date as Date
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.flight import FlightResponse, RoundTripResponse
from app.schemas.airport import AirportResponse
from app.schemas.grade import GradeResponse
from app.schemas.promotion import PromotionResponse
from app.schemas.member import RouteRecommendation

ChatTopic = Literal[
    "flights",
    "promotions",
    "grades",
    "popular_routes",
    "frequent_routes",
    "inquiry_guide",
]


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=20, ge=1, le=50)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=10)
    context: "ChatContext | None" = None

    @model_validator(mode="after")
    def validate_history(self):
        if sum(len(message.content) for message in self.history) > 10000:
            raise ValueError("이전 대화는 총 10,000자 이내로 전달해 주세요.")
        return self


class FlightConditions(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    departure: str | None = Field(default=None, min_length=1, max_length=100)
    arrival: str | None = Field(default=None, min_length=1, max_length=100)
    date: Date | None = None
    trip_type: Literal["one_way", "round_trip"] = "one_way"
    return_date: Date | None = None
    return_date_from: Date | None = None
    return_date_to: Date | None = None
    airline: str | None = Field(default=None, min_length=1, max_length=100)
    exclude_airlines: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        default_factory=list, max_length=10
    )
    min_price: int | None = Field(default=None, ge=0, le=2147483647)
    max_price: int | None = Field(default=None, ge=0, le=2147483647)
    seat_class: Literal["이코노미", "비즈니스", "퍼스트"] | None = None
    departure_from: datetime | None = None
    departure_to: datetime | None = None
    arrival_from: datetime | None = None
    arrival_to: datetime | None = None
    return_departure_from: datetime | None = None
    return_departure_to: datetime | None = None
    return_arrival_from: datetime | None = None
    return_arrival_to: datetime | None = None
    sort_by: Literal["departure_at", "arrival_at", "price", "return_departure_at"] = "departure_at"
    sort_order: Literal["asc", "desc"] = "asc"


class SearchSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conditions: FlightConditions
    max_results: int | None = Field(default=None, ge=1, le=50)
    result_kind: Literal["flights", "destinations"] = "flights"


class ChatContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    searches: list[SearchSnapshot] = Field(default_factory=list, max_length=5)
    pending_field: (
        Literal["departure", "arrival", "date", "return_date", "airline"] | None
    ) = None
    pending_options: list[str] = Field(default_factory=list, max_length=10)
    pending_offer: Literal["change_search", "base_price_search", "confirm_time"] | None = None
    pending_search: SearchSnapshot | None = None


class ExtractedConditions(FlightConditions):
    date: str | None = Field(default=None, max_length=30)
    return_date: str | None = Field(default=None, max_length=30)
    return_date_from: str | None = Field(default=None, max_length=30)
    return_date_to: str | None = Field(default=None, max_length=30)
    departure_from: str | None = Field(default=None, max_length=50)
    departure_to: str | None = Field(default=None, max_length=50)
    arrival_from: str | None = Field(default=None, max_length=50)
    arrival_to: str | None = Field(default=None, max_length=50)
    return_departure_from: str | None = Field(default=None, max_length=50)
    return_departure_to: str | None = Field(default=None, max_length=50)
    return_arrival_from: str | None = Field(default=None, max_length=50)
    return_arrival_to: str | None = Field(default=None, max_length=50)


ConditionField = Literal[
    "departure",
    "arrival",
    "date",
    "trip_type",
    "return_date",
    "return_date_from",
    "return_date_to",
    "airline",
    "exclude_airlines",
    "min_price",
    "max_price",
    "seat_class",
    "departure_from",
    "departure_to",
    "arrival_from",
    "arrival_to",
    "return_departure_from",
    "return_departure_to",
    "return_arrival_from",
    "return_arrival_to",
    "sort_by",
    "sort_order",
]

ReasonCode = Literal[
    "discount_calculation",
    "multiple_promotions",
    "duration",
    "return_time",
    "connections",
    "passengers",
    "private_data",
    "mutation",
    "external_data",
    "security",
    "recurring_time",
    "out_of_scope",
    "invalid_date",
    "invalid_price",
    "missing_context",
    "ambiguous_time",
    "promotion_period",
    "time_confirmation",
    "local_time",
]


class ChatPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "needs_clarification", "unsupported"]
    topics: list[ChatTopic] = Field(max_length=6)
    conditions: FlightConditions
    clarification: str | None = Field(default=None, max_length=300)
    max_results: int | None = Field(default=None, ge=1, le=50)
    action: Literal["new", "update", "restore"] = "new"
    changed_fields: list[ConditionField] = Field(default_factory=list, max_length=23)
    clear_fields: list[ConditionField] = Field(default_factory=list, max_length=23)
    confirm_time: bool = False
    restore_index: int | None = Field(default=None, ge=0, le=4)
    reason: ReasonCode | None = None
    result_kind: Literal["flights", "destinations"] = "flights"
    dialogue_act: Literal["decline", "accept", "acknowledge", "clarify", "reset_search"] | None = None
    promotion_request: (
        Literal["current", "travel_period", "discounted_price", "stacking"] | None
    ) = None
    promotion_evidence: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_state(self):
        if self.status == "ready" and not self.topics and self.dialogue_act is None:
            raise ValueError("조회 주제가 필요함.")
        if self.status == "needs_clarification" and not self.clarification:
            raise ValueError("추가 질문이 필요함.")
        if len(set(self.topics)) != len(self.topics):
            raise ValueError("주제가 중복됨.")
        return self


class LocationSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: Literal["departure", "arrival"]
    text: str = Field(min_length=1, max_length=100)


class ExtractedPlan(ChatPlan):
    conditions: ExtractedConditions
    location_sources: list[LocationSource] = Field(default_factory=list, max_length=2)


class ClarificationOption(BaseModel):
    label: str
    value: str


class Clarification(BaseModel):
    field: str | None = None
    prompt: str
    options: list[ClarificationOption] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reset_search: bool = False
    request_id: str
    status: Literal["success", "needs_clarification", "unsupported"]
    message: str
    topics: list[ChatTopic]
    interpreted_conditions: dict = Field(default_factory=dict)
    clarification: Clarification | None = None
    count: int = 0
    limit: int
    has_more: bool = False
    flights: list[FlightResponse] = Field(default_factory=list)
    round_trips: list[RoundTripResponse] = Field(default_factory=list)
    promotions: list[PromotionResponse] = Field(default_factory=list)
    grades: list[GradeResponse] = Field(default_factory=list)
    destinations: list[AirportResponse] = Field(default_factory=list)
    popular_routes: list[RouteRecommendation] = Field(default_factory=list)
    frequent_routes: list[RouteRecommendation] = Field(default_factory=list)
    navigation: list[Literal["inquiry_create", "login"]] = Field(default_factory=list)
    context: ChatContext = Field(default_factory=ChatContext)
    reason: str | None = None


ChatRequest.model_rebuild()
