from fastapi import HTTPException
from app.services.airline_filters import (
    resolve_airline as _resolve_airline,
    excluded_airline_ids,
)
from sqlalchemy.orm import Session

from app.core.time import local_datetime, now_local
from app.core.database import start_chat_read_only
from app.services.chat_dialogue import dialogue_message
from app.services.chat_routes import answer_routes, INQUIRY_GUIDE
from app.schemas.chatbot import ChatPlan, ChatRequest, ChatResponse, Clarification
from app.schemas.airport import AirportResponse
from app.services.chat_context import prepare_plan, remember
from app.services.chat_locations import resolve_location
from app.services.chat_policy import REASONS
from app.services.chat_times import time_summary
from app.schemas.flight import FlightResponse, RoundTripResponse
from app.schemas.grade import GradeResponse
from app.schemas.promotion import PromotionResponse
from app.services.catalog import list_grades, list_promotions
from app.services.flights import search_flights
from app.services.round_trips import search_round_trips
from app.services.return_dates import resolve_return_dates


def _clarify(response: ChatResponse, field: str, prompt: str, options=None):
    response.status = "needs_clarification"
    response.message = prompt
    response.clarification = Clarification(
        field=field, prompt=prompt, options=options or []
    )
    return response


def _prepare_flight_conditions(db, conditions, response):
    is_round_trip = (
        conditions.trip_type == "round_trip" or conditions.return_date is not None
        or conditions.return_date_from is not None or conditions.return_date_to is not None
    )
    if is_round_trip:
        conditions.trip_type = "round_trip"
        if conditions.date is None or not (conditions.return_date or conditions.return_date_from):
            return _clarify(
                response,
                "return_date",
                "왕복 항공편을 찾아드릴게요. 가는 날과 돌아오는 날짜 또는 기간을 알려주시겠어요?",
            )
        try:
            start, end = resolve_return_dates(conditions.date, conditions.return_date,
                                             conditions.return_date_from, conditions.return_date_to)
        except HTTPException as exc:
            return _clarify(response, "return_date", exc.detail)
        if conditions.return_date is None:
            conditions.return_date_from, conditions.return_date_to = start, end
    elif conditions.sort_by == "return_departure_at":
        conditions.sort_by = "departure_at"
    resolved = {}
    for field, label in (("departure", "출발"), ("arrival", "도착")):
        value = getattr(conditions, field)
        if not value:
            continue
        candidates, kind = resolve_location(db, value)
        if (
            not candidates
            or kind == "suggestion"
            or (kind == "airport" and len(candidates) > 1)
        ):
            prompt = (
                f"{label} 공항으로 아래 공항을 말씀하신 걸까요?"
                if candidates
                else f"‘{value}’에 해당하는 {label} 공항을 찾지 못했어요. 도시나 공항 이름을 다시 알려주시겠어요?"
            )
            return _clarify(
                response,
                field,
                prompt,
                [
                    {
                        "label": airport.name_ko,
                        "value": airport.iata_code or airport.icao_code,
                    }
                    for airport in candidates[:10]
                ],
            )
        resolved[field + "_ids"] = [airport.airport_id for airport in candidates]
        if len(candidates) == 1:
            setattr(
                conditions, field, candidates[0].iata_code or candidates[0].icao_code
            )
    if conditions.departure and conditions.departure == conditions.arrival:
        return _clarify(
            response,
            "arrival",
            "출발지와 도착지가 같은 공항이에요. 어느 공항으로 가실 예정인가요?",
        )
    if conditions.date is not None and conditions.date < now_local().date():
        return _clarify(
            response,
            "date",
            "이미 지난 날짜예요. 오늘 이후로 원하시는 탑승일을 알려주세요.",
        )
    if conditions.airline:
        candidates = _resolve_airline(db, conditions.airline)
        if len(candidates) != 1 or not (
            candidates[0].iata_code or candidates[0].icao_code
        ):
            return _clarify(
                response, "airline", "항공사 이름이나 코드를 확인해 주세요."
            )
        conditions.airline = candidates[0].iata_code or candidates[0].icao_code
    try:
        resolved["excluded_ids"] = excluded_airline_ids(
            db, conditions.exclude_airlines, conditions.airline
        )
    except HTTPException as exc:
        return _clarify(response, "airline", exc.detail)
    for lower_name, upper_name in (
        ("departure_from", "departure_to"),
        ("arrival_from", "arrival_to"),
        ("return_departure_from", "return_departure_to"),
        ("return_arrival_from", "return_arrival_to"),
    ):
        for name in (lower_name, upper_name):
            value = getattr(conditions, name)
            if value is not None:
                setattr(conditions, name, local_datetime(value))
        lower, upper = (
            getattr(conditions, lower_name),
            getattr(conditions, upper_name),
        )
        if lower and upper and lower > upper:
            return _clarify(
                response, lower_name, "조회 시작 시각과 종료 시각을 확인해 주세요."
            )
    return resolved


def _answer_flights(db, plan, response):
    conditions = plan.conditions.model_copy(deep=True)
    problem = _prepare_flight_conditions(db, conditions, response)
    if isinstance(problem, ChatResponse):
        return problem
    resolved = problem
    is_round_trip = conditions.trip_type == "round_trip"
    query = conditions.model_dump(exclude={"trip_type", "return_date"})
    query["travel_date"] = query.pop("date")
    query.update(resolved)
    for field in ("departure", "arrival"):
        if field + "_ids" in resolved:
            query[field] = None
    if plan.result_kind == "destinations" and is_round_trip:
        response.status = "unsupported"
        response.message = "갈 수 있는 공항 목록은 현재 편도 기준으로 안내해 드려요. 왕복은 항공편 조합으로 검색해 주세요."
        return response
    if is_round_trip:
        result = search_round_trips(
            db=db,
            **query,
            return_date=conditions.return_date,
            limit=response.limit + 1,
            include_total=False,
            offset=0,
        )
        response.round_trips = [
            RoundTripResponse.model_validate(row)
            for row in result["round_trips"][: response.limit]
        ]
    else:
        for key in tuple(query):
            if key.startswith("return_"):
                query.pop(key)
        result = search_flights(
            db=db,
            **query,
            flight_status=None,
            bookable_only=True,
            destinations_only=plan.result_kind == "destinations",
            limit=response.limit + 1,
            include_total=False,
            offset=0,
        )
        if plan.result_kind == "destinations":
            response.destinations = [
                AirportResponse.model_validate(row)
                for row in result["destinations"][: response.limit]
            ]
        else:
            response.flights = [
                FlightResponse.model_validate(row)
                for row in result["flights"][: response.limit]
            ]
    response.interpreted_conditions = conditions.model_dump(
        mode="json", exclude_none=True
    )
    response.interpreted_conditions["bookable_only"] = True
    response.count = min(result["count"], response.limit)
    response.has_more = result["count"] > response.limit
    if plan.result_kind == "destinations":
        scope = "전체 출발지 기준으로 " if not conditions.departure else ""
        response.message = (
            f"{scope}지금 조건으로 갈 수 있는 도착 공항 {response.count}곳을 찾았어요.\n"
            + "\n".join(
                f"{a.name_ko} ({a.iata_code or a.icao_code})"
                for a in response.destinations
            )
            if response.count
            else "지금 조건으로 예약 가능한 항공편이 있는 도착 공항을 찾지 못했어요."
        )
    elif is_round_trip:
        response.message = (
            f"조건에 맞는 왕복 항공편 {response.count}개 조합을 찾았어요. 표시된 금액은 1인 왕복 기본 요금이에요. 가는 편과 오는 편의 좌석은 예약할 때 함께 확정돼요."
            if response.count
            else "지금 조건으로는 예약 가능한 왕복 항공편을 찾지 못했어요. 여행 날짜나 공항 조건을 바꿔서 다시 찾아볼까요?"
        )
        summary = time_summary(conditions)
        if conditions.return_date_from:
            response.message += (
                f"\n조회한 귀국편 출발 기간: {conditions.return_date_from:%Y-%m-%d} ~ "
                f"{conditions.return_date_to:%Y-%m-%d} (양 끝 날짜 포함, 한국 시간)."
                " 출국편 도착 이후에 출발하는 귀국편만 조회했어요."
            )
        if summary:
            response.message += f"\n\n적용한 시간 조건 (한국 시간)\n{summary}"
    else:
        response.message = (
            f"조건에 맞는 항공편 {response.count}건을 찾았어요. 표시된 금액은 1인 기본 요금이고, 좌석은 예약할 때 확정돼요."
            if response.count
            else _empty_flights_message(conditions)
        )
        if (
            response.flights
            and conditions.sort_by == "price"
            and conditions.sort_order == "asc"
        ):
            first = response.flights[0]
            response.message = (
                f"요청하신 조건에서 가장 낮은 기본 요금은 1인 {first.base_price:,}원이에요. "
                f"{first.departure_at:%Y년 %m월 %d일 %H:%M} 출발, "
                f"{first.departure_airport.name_ko} → {first.arrival_airport.name_ko} 항공편이에요. "
                "표시 시각은 한국 시각이며 할인 전 금액이에요. 같은 최저 요금의 다른 항공편이 있을 수 있고, 좌석은 예약할 때 확정돼요."
            )
    return response


def _answer_promotions(db):
    rows = list_promotions(db, ending_first=True)
    items = [PromotionResponse.model_validate(row) for row in rows]
    if rows:
        message = (
            "지금 이용할 수 있는 프로모션을 안내해 드릴게요.\n"
            + "\n".join(
                f"{row.promotion_name} — {row.discount_rate:g}% 할인, "
                f"{row.start_at:%Y-%m-%d %H:%M} ~ {row.end_at:%Y-%m-%d %H:%M}(한국 시각)"
                for row in rows
            )
            + "\n위 기간은 탑승일이 아니라 예약 시점의 적용 기간이에요. 할인 적용 여부는 예약할 때 다시 확인해 드려요."
        )
    else:
        message = "현재 진행 중인 프로모션은 없어요."
    return items, message


def _answer_grades(db):
    rows = list_grades(db)
    items = [GradeResponse.model_validate(row) for row in rows]
    message = (
        "회원 등급별 기준과 적립률을 안내해 드릴게요.\n"
        + "\n".join(
            f"{row.grade_name}({row.grade_code}) — 등록된 승급 기준 {row.upgrade_requirement}, "
            f"포인트 적립률 {row.point_rate:g}%"
            for row in rows
        )
        + "\n포인트는 회원의 최종 결제 금액을 기준으로 적립돼요. 현재 자동 등급 승급은 지원하지 않아요."
        if rows
        else "아직 등록된 회원 등급 정보가 없어요."
    )
    return items, message


def _answer_plan(
    db: Session,
    plan: ChatPlan,
    payload: ChatRequest,
    request_id: str,
    current_member=None,
):
    response = ChatResponse(
        request_id=request_id,
        status="success",
        message="",
        topics=plan.topics,
        reason=plan.reason,
        limit=min(payload.limit, plan.max_results or payload.limit),
    )
    if plan.dialogue_act:
        response.message = dialogue_message(plan.dialogue_act, payload.context)
        if plan.dialogue_act in ("accept", "clarify"):
            return _clarify(response, "question", response.message)
        return response
    if plan.status == "unsupported":
        response.status = "unsupported"
        response.message = REASONS.get(plan.reason, REASONS["out_of_scope"])
        return response
    if plan.reason == "time_confirmation":
        return _clarify(
            response, "time",
            f"아래 시간 조건으로 찾아드릴까요? 모두 한국 시간 기준이에요.\n{time_summary(plan.conditions)}\n원하시는 조건이면 ‘네’, 다르면 원하는 날짜와 시간을 알려주세요.",
            [{"label": "이 시간으로 검색", "value": "네"}],
        )
    if plan.status == "needs_clarification":
        return _clarify(
            response,
            "date" if plan.reason in ("invalid_date", "ambiguous_time") else "question",
            REASONS.get(plan.reason, plan.clarification),
        )

    messages = []
    messages.extend(answer_routes(db, response, current_member))
    if "inquiry_guide" in plan.topics:
        response.navigation.append("inquiry_create")
        messages.append(INQUIRY_GUIDE)
    if "flights" in plan.topics:
        _answer_flights(db, plan, response)
        if response.status != "success":
            return response
        messages.append(response.message)
    if "promotions" in plan.topics:
        response.promotions, message = _answer_promotions(db)
        messages.append(message)
    if "grades" in plan.topics:
        response.grades, message = _answer_grades(db)
        messages.append(message)
    response.message = "\n\n".join(messages)
    return response


def answer_plan(
    db: Session,
    plan: ChatPlan,
    payload: ChatRequest,
    request_id: str,
    current_member=None,
):
    prepared = prepare_plan(plan, payload)
    if prepared.status == "ready" and not prepared.dialogue_act:
        start_chat_read_only(db)
    response = _answer_plan(db, prepared, payload, request_id, current_member)
    return remember(response, prepared, payload)


def _empty_flights_message(conditions):
    if conditions.min_price is not None or conditions.max_price is not None:
        return "지금 조건으로 예약 가능한 항공편을 찾지 못했어요. 가격 범위를 바꿔서 다시 찾아볼까요?"
    if conditions.date or any(
        (
            conditions.departure_from,
            conditions.departure_to,
            conditions.arrival_from,
            conditions.arrival_to,
        )
    ):
        return "지금 조건으로 예약 가능한 항공편을 찾지 못했어요. 다른 날짜나 목적지도 찾아볼까요?"
    return "현재 등록된 항공편 중 조건에 맞는 예약 가능한 항공편을 찾지 못했어요. 다른 목적지도 찾아볼까요?"
