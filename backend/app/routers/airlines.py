from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.airline import Airline
from app.schemas.airline import AirlineListResponse

router = APIRouter(prefix="/airlines", tags=["airlines"])


@router.get("", response_model=AirlineListResponse)
def get_airlines(
    keyword: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Airline)

    if keyword:
        keyword = keyword.strip()
        search = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Airline.iata_code == keyword.upper(),
                Airline.icao_code == keyword.upper(),
                Airline.name_ko.like(search),
                Airline.name_en.like(search),
                Airline.country.like(search),
            )
        )

    stmt = stmt.order_by(Airline.country, Airline.name_en).offset(offset).limit(limit)
    airlines = db.scalars(stmt).all()
    return {"count": len(airlines), "airlines": airlines}
