from pydantic import BaseModel, ConfigDict


class AirportResponse(BaseModel):
    airport_id: int
    name_ko: str
    name_en: str
    iata_code: str | None
    icao_code: str | None
    country: str
    city: str

    model_config = ConfigDict(from_attributes=True)


class AirportListResponse(BaseModel):
    count: int
    airports: list[AirportResponse]
