from fastapi import HTTPException
from sqlalchemy import select, or_, func

from app.models.airline import Airline


def resolve_airline(db, value):
    code = value.strip().upper()
    name = value.casefold().replace(" ", "")
    return db.scalars(
        select(Airline).where(
            or_(
                Airline.iata_code == code,
                Airline.icao_code == code,
                func.replace(func.lower(Airline.name_ko), " ", "") == name,
                func.replace(func.lower(Airline.name_en), " ", "") == name,
            )
        )
    ).all()


def excluded_airline_ids(db, values, included=None):
    ids = set()
    for value in values or []:
        rows = resolve_airline(db, value)
        if len(rows) != 1:
            raise HTTPException(400, "제외할 항공사 이름 또는 코드를 확인해 주세요.")
        ids.add(rows[0].airline_id)
    if included and ids:
        if any(row.airline_id in ids for row in resolve_airline(db, included)):
            raise HTTPException(400, "같은 항공사를 포함하고 제외할 수 없어요.")
    return sorted(ids)
