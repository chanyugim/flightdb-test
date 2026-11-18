import re
from datetime import date, datetime, time

from app.core.time import local_datetime


TIME_GROUPS = (
    ("departure", "date", "가는 편 출발"),
    ("arrival", "date", "가는 편 도착"),
    ("return_departure", "return_date", "오는 편 출발"),
    ("return_arrival", "return_date", "오는 편 도착"),
)
TIME_FIELDS = tuple(f"{prefix}_{bound}" for prefix, _, _ in TIME_GROUPS for bound in ("from", "to"))
RETURN_TIME_FIELDS = tuple(field for field in TIME_FIELDS if field.startswith("return_"))


def needs_time_confirmation(question, conditions, previous):
    vague = any(
        not re.match(r"\s*(?:\d|[한두세네다섯여섯일곱여덟아홉열]+\s*시)", question[match.end():])
        for match in re.finditer(r"오전|오후|저녁|새벽", question)
    )
    return vague and any(
        getattr(conditions, key) is not None
        and (not previous or getattr(conditions, key) != getattr(previous.conditions, key))
        for key in TIME_FIELDS
    )


def complete_times(values):
    for prefix, day_field, _ in TIME_GROUPS:
        for bound in ("from", "to"):
            key = f"{prefix}_{bound}"
            value = values.get(key)
            if isinstance(value, str) and re.fullmatch(r"\d{2}:\d{2}(?::\d{2})?", value):
                # 도착 시각만으로 출발 당일 도착을 가정하지 않음.
                if "arrival" in prefix or not values.get(day_field):
                    return "ambiguous_time"
                try:
                    values[key] = datetime.combine(
                        date.fromisoformat(values[day_field]), time.fromisoformat(value)
                    ).isoformat()
                except ValueError:
                    return "invalid_date"
    return None


def shift_times(values, previous, fields, clears):
    for prefix, day_field, _ in TIME_GROUPS:
        old_day = getattr(previous.conditions, day_field)
        new_day = values.get(day_field)
        if not old_day or not new_day:
            continue
        try:
            shift = date.fromisoformat(new_day) - old_day
        except ValueError:
            return "invalid_date"
        if not shift:
            continue
        for bound in ("from", "to"):
            key = f"{prefix}_{bound}"
            old_value = getattr(previous.conditions, key)
            if key not in fields and key not in clears and old_value:
                values[key] = (old_value + shift).isoformat()
    return None


def time_summary(conditions):
    lines = []
    for prefix, _, label in TIME_GROUPS:
        lower = getattr(conditions, f"{prefix}_from")
        upper = getattr(conditions, f"{prefix}_to")
        if not lower and not upper:
            continue
        start = local_datetime(lower).strftime("%Y-%m-%d %H:%M") if lower else None
        end = local_datetime(upper).strftime("%Y-%m-%d %H:%M") if upper else None
        span = f"{start} ~ {end}" if start and end else f"{start} 이후" if start else f"{end} 이전"
        lines.append(f"{label}: {span}")
    return "\n".join(lines)
