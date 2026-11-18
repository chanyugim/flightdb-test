from datetime import datetime, timedelta

from app.core.time import local_datetime


def calendar_context(current_time: str):
    current = local_datetime(datetime.fromisoformat(current_time)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    monday = current - timedelta(days=current.weekday())
    next_month = (current.replace(day=1) + timedelta(days=32)).replace(day=1)
    month_after = (next_month + timedelta(days=32)).replace(day=1)
    periods = {
        "next_week": (monday + timedelta(days=7), monday + timedelta(days=14)),
        "this_weekend": (monday + timedelta(days=5), monday + timedelta(days=7)),
        "next_month": (next_month, month_after),
    }
    return {
        key: {
            "from": start.isoformat(),
            "to": (end - timedelta(microseconds=1)).isoformat(),
        }
        for key, (start, end) in periods.items()
    }
