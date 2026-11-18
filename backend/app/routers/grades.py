from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.grade import GradeResponse
from app.services.catalog import list_grades

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("", response_model=list[GradeResponse])
def get_grades(db: Session = Depends(get_db)):
    return list_grades(db)
