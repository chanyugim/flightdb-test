from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PromotionResponse(BaseModel):
    promotion_id: int
    promotion_name: str
    discount_rate: Decimal
    start_at: datetime
    end_at: datetime

    model_config = ConfigDict(from_attributes=True)
