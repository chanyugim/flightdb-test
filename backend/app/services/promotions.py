from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.promotion import Promotion
from app.models.reservation import Reservation
from app.schemas.admin import (
    PromotionCreateRequest,
    PromotionUpdateRequest,
)


def list_admin_promotions(db: Session, limit: int, offset: int):
    return db.scalars(
        select(Promotion)
        .order_by(Promotion.start_at.desc(), Promotion.promotion_id)
        .offset(offset)
        .limit(limit)
    ).all()


def delete_promotion(db: Session, promotion_id: int):
    promotion = db.scalar(select(Promotion).where(Promotion.promotion_id == promotion_id).with_for_update())
    if promotion is None:
        raise HTTPException(status_code=404, detail="프로모션을 찾을 수 없습니다.")
    if db.scalar(select(Reservation.reservation_no).where(Reservation.promotion_id == promotion_id).limit(1)):
        raise HTTPException(status_code=409, detail="예약에 사용된 프로모션은 삭제할 수 없습니다. 적용 기간을 수정해 주세요.")
    db.delete(promotion)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="예약에 사용된 프로모션은 삭제할 수 없습니다.") from exc
    return {"message": "프로모션을 삭제했습니다."}


def create_promotion(db: Session, payload: PromotionCreateRequest):
    if payload.start_at > payload.end_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_at must be before or equal to end_at",
        )
    promotion = Promotion(
        promotion_name=payload.promotion_name,
        discount_rate=payload.discount_rate,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    return promotion


def update_promotion(db: Session, promotion_id: int, payload: PromotionUpdateRequest):
    promotion = db.scalar(
        select(Promotion)
        .where(Promotion.promotion_id == promotion_id)
        .with_for_update()
    )
    if promotion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found"
        )
    start_at = payload.start_at if payload.start_at is not None else promotion.start_at
    end_at = payload.end_at if payload.end_at is not None else promotion.end_at
    if start_at > end_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_at must be before or equal to end_at",
        )
    if payload.promotion_name is not None:
        promotion.promotion_name = payload.promotion_name
    if payload.discount_rate is not None:
        promotion.discount_rate = payload.discount_rate
    if payload.start_at is not None:
        promotion.start_at = payload.start_at
    if payload.end_at is not None:
        promotion.end_at = payload.end_at
    db.commit()
    db.refresh(promotion)
    return promotion
