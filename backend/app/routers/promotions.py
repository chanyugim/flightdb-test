from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.promotion import PromotionResponse
from app.services.catalog import list_promotions

router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.get("", response_model=list[PromotionResponse])
def get_promotions(
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return list_promotions(db, active_only=active_only, limit=limit, offset=offset)
