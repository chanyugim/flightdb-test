from datetime import timedelta

from fastapi import HTTPException


def resolve_return_dates(travel_date, return_date=None, return_date_from=None, return_date_to=None):
    if return_date and (return_date_from or return_date_to):
        raise HTTPException(400, "귀국 날짜와 귀국 기간 중 하나만 지정해 주세요.")
    start = return_date or return_date_from
    if not start:
        raise HTTPException(400, "돌아오는 날짜 또는 기간의 시작 날짜를 알려주세요.")
    end = return_date or return_date_to or start + timedelta(days=29)
    if start < travel_date or end < start:
        raise HTTPException(400, "귀국 기간은 출국일 이후이며 시작일보다 종료일이 빠를 수 없어요.")
    if (end - start).days >= 30:
        raise HTTPException(400, "귀국 검색 기간은 최대 30일까지 지정해 주세요.")
    return start, end
