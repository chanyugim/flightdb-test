from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.airports import search_airports
from app.schemas.airport import AirportListResponse

router = APIRouter(prefix="/airports", tags=["airports"])


@router.get("", response_model=AirportListResponse)
def get_airports(
    keyword: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    selectable_only: bool = False,
    db: Session = Depends(get_db),
):
    return search_airports(
        db, keyword=keyword, limit=limit, offset=offset, selectable_only=selectable_only
    )
