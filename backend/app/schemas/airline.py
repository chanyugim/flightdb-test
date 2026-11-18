from pydantic import BaseModel, ConfigDict


class AirlineResponse(BaseModel):
    airline_id: int
    name_ko: str
    name_en: str
    iata_code: str | None
    icao_code: str | None
    country: str

    model_config = ConfigDict(from_attributes=True)


class AirlineListResponse(BaseModel):
    count: int
    airlines: list[AirlineResponse]
