import unicodedata

from sqlalchemy import case, func, or_, select

from app.models.airport import Airport
from app.services.location_aliases import (
    CITY_ALIASES,
    COUNTRY_ALIASES,
    REGIONS,
    compact_location,
    country_names,
)


def _compact(column):
    return func.replace(func.lower(column), " ", "")


def search_airports(db, *, keyword=None, limit=20, offset=0, selectable_only=False):
    stmt = select(Airport)
    if selectable_only:
        stmt = stmt.where(
            or_(
                func.length(func.trim(Airport.iata_code)) > 0,
                func.length(func.trim(Airport.icao_code)) > 0,
            )
        )
    keyword = unicodedata.normalize("NFC", keyword or "").strip()
    exact_code = or_(
        func.upper(Airport.iata_code) == keyword.upper(),
        func.upper(Airport.icao_code) == keyword.upper(),
    )
    if keyword:
        key = compact_location(keyword)
        countries = country_names(key)
        if countries:
            match = _compact(Airport.country).in_(
                [compact_location(name) for name in countries]
            )
        elif key in CITY_ALIASES:
            match = _compact(Airport.city).in_(
                [compact_location(CITY_ALIASES[key]), key]
            )
        elif key in REGIONS:
            match = Airport.iata_code.in_(REGIONS[key])
        else:
            # LIKE의 %, _는 검색 명령이 아니라 사용자가 입력한 문자로 취급함.
            matches = [
                _compact(column).contains(key, autoescape=True)
                for column in (
                    Airport.name_ko,
                    Airport.name_en,
                    Airport.city,
                    Airport.country,
                )
            ]
            if not key.isascii():
                cities = {
                    compact_location(city)
                    for alias, city in CITY_ALIASES.items()
                    if alias.startswith(key)
                }
                countries = {
                    compact_location(name)
                    for alias in COUNTRY_ALIASES
                    if alias.startswith(key)
                    for name in country_names(alias)
                }
                if cities:
                    matches.append(_compact(Airport.city).in_(cities))
                if countries:
                    matches.append(_compact(Airport.country).in_(countries))
            match = or_(*matches)
        stmt = stmt.where(or_(exact_code, match)).order_by(
            case((exact_code, 0), else_=1)
        )
    stmt = stmt.order_by(
        Airport.country, Airport.city, Airport.name_en, Airport.airport_id
    )
    airports = db.scalars(stmt.offset(offset).limit(limit)).all()
    return {"count": len(airports), "airports": airports}
