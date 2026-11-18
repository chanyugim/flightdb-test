from pydantic import BaseModel, ConfigDict


class SeatResponse(BaseModel):
    seat_id: int
    flight_id: int
    seat_no: str
    seat_class: str
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class SeatListResponse(BaseModel):
    count: int
    seats: list[SeatResponse]
