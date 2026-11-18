from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class GradeResponse(BaseModel):
    grade_code: str
    grade_name: str
    upgrade_requirement: int
    point_rate: Decimal

    model_config = ConfigDict(from_attributes=True)
