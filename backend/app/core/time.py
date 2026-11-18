"""시드 데이터와 업무 시각은 한국 표준시를 사용함."""

from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def local_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(KST).replace(tzinfo=None)
    return value


def now_local() -> datetime:
    return datetime.now(KST).replace(tzinfo=None)
