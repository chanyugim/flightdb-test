import re
import unicodedata
from difflib import SequenceMatcher

from sqlalchemy import func, or_, select

from app.models.airport import Airport
from app.services.location_aliases import CITY_ALIASES, REGIONS, country_names


def normalize(value):
    value = unicodedata.normalize("NFC", value).casefold().strip()
    for suffix in ("국제공항", "공항", "international airport", "airport"):
        value = value.replace(suffix, "")
    return re.sub(r"\s+", "", value)


def similarity(left, right):
    return max(
        SequenceMatcher(None, left, right).ratio(),
        0.9
        * SequenceMatcher(
            None,
            unicodedata.normalize("NFD", left),
            unicodedata.normalize("NFD", right),
        ).ratio(),
    )


def coded_airports():
    return select(Airport).where(
        or_(Airport.iata_code.is_not(None), Airport.icao_code.is_not(None))
    )


def resolve_location(db, value):
    original = unicodedata.normalize("NFC", value).strip()
    key = normalize(original)
    code = original.upper()
    if code.isascii() and code.isalnum() and 2 <= len(code) <= 4:
        rows = db.scalars(
            coded_airports().where(
                or_(Airport.iata_code == code, Airport.icao_code == code)
            )
        ).all()
        if rows:
            return rows, "airport"
    if key in REGIONS:
        return db.scalars(
            coded_airports().where(Airport.iata_code.in_(REGIONS[key]))
        ).all(), "region"
    countries = country_names(key) or (original.casefold(),)
    rows = db.scalars(
        coded_airports()
        .where(func.lower(Airport.country).in_(countries))
        .order_by(Airport.airport_id)
    ).all()
    if rows:
        return rows, "country"
    city = CITY_ALIASES.get(key, original.casefold())
    rows = db.scalars(
        coded_airports()
        .where(func.lower(Airport.city) == city)
        .order_by(Airport.airport_id)
    ).all()
    if rows:
        return rows, "city"
    for region in REGIONS:
        if key.startswith(region) and len(key) > len(region):
            key = key[len(region) :]
            break
    ko = func.replace(
        func.replace(func.replace(Airport.name_ko, "국제공항", ""), "공항", ""), " ", ""
    )
    en = func.replace(
        func.replace(
            func.replace(func.lower(Airport.name_en), "international airport", ""),
            "airport",
            "",
        ),
        " ",
        "",
    )
    rows = db.scalars(
        coded_airports().where(or_(ko == key, en == key)).order_by(Airport.airport_id)
    ).all()
    if rows:
        return rows, "airport"
    if not key or not re.fullmatch(r"[a-z가-힣]+", key):
        return [], "unknown"
    prefix = key[:1] if not key.isascii() else key[:3]
    candidates = db.scalars(
        coded_airports()
        .where(or_(ko.startswith(prefix), en.startswith(prefix)))
        .limit(50)
    ).all()
    scored = [
        (
            max(
                similarity(key, normalize(row.name_ko)),
                similarity(key, normalize(row.name_en)),
            ),
            row,
        )
        for row in candidates
    ]
    return [
        row
        for score, row in sorted(scored, key=lambda item: item[0], reverse=True)
        if score >= 0.65
    ][:5], "suggestion"
