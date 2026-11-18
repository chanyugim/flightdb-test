import re
from datetime import date
from decimal import Decimal

from pydantic import ValidationError
from app.core.calendar import calendar_context
from app.core.time import local_datetime, now_local

from app.schemas.chatbot import ChatContext, ChatPlan, FlightConditions, SearchSnapshot
from app.services.chat_policy import REASONS, explicit_dates, guard_question
from app.services.chat_dialogue import prepare_dialogue, normalize_promotion_request
from app.services.chat_times import TIME_GROUPS, TIME_FIELDS, RETURN_TIME_FIELDS, complete_times, shift_times, needs_time_confirmation


def clarification(reason, conditions=None):
    return ChatPlan(
        status="needs_clarification",
        topics=["flights"],
        conditions=FlightConditions.model_validate(conditions or {}),
        clarification=REASONS[reason],
        reason=reason,
    )


def prepare_plan(plan, payload):
    question = payload.question
    reason = guard_question(question)
    if reason:
        if reason == "invalid_date":
            return clarification(reason)
        return ChatPlan(
            status="unsupported",
            topics=[],
            conditions=FlightConditions(),
            reason=reason,
        )
    selection = selection_plan(payload)
    if selection is not None:
        plan = selection
    dialogue = prepare_dialogue(plan, payload)
    if dialogue is not None:
        if dialogue.dialogue_act:
            return dialogue
        plan = dialogue
    plan = normalize_promotion_request(plan, question)
    if "flights" not in plan.topics:
        return ChatPlan.model_validate(
            {
                **plan.model_dump(exclude={"conditions", "location_sources"}),
                "conditions": FlightConditions(),
            }
        )
    snapshots = payload.context.searches if payload.context else []
    previous = snapshots[-1] if snapshots else None
    if payload.context and payload.context.pending_search:
        previous = payload.context.pending_search
    reset = bool(
        re.search(
            r"처음부터|새\s*검색|새로운\s*검색|이전\s*조건.*(?:없애|무시|초기화)|전체\s*항공편\s*중",
            question,
        )
    )
    if previous and plan.action == "new" and not reset:
        defaults = FlightConditions().model_dump(mode="json")
        extracted = plan.conditions.model_dump(mode="json")
        fields = set(plan.changed_fields)
        fields.update(
            key
            for key, value in extracted.items()
            if value != defaults[key] and value is not None
        )
        plan = plan.model_copy(
            update={"action": "update", "changed_fields": list(fields)}
        )
    if plan.action == "restore":
        if plan.restore_index is None or plan.restore_index >= len(snapshots):
            return clarification("missing_context")
        previous = snapshots[plan.restore_index]
    updating = previous is not None and plan.action in ("update", "restore")
    values = (
        previous.conditions.model_dump(mode="json")
        if updating
        else FlightConditions().model_dump(mode="json")
    )
    extracted = plan.conditions.model_dump(mode="json")
    for source in getattr(plan, "location_sources", []):
        if source.text in question:
            extracted[source.field] = source.text
    fields = set(plan.changed_fields) if updating else set(extracted)
    clears = set(plan.clear_fields)
    airline_reset = bool(
        re.search(
            r"(?:항공사|항공|[A-Z0-9]{2,3}).{0,25}(?:상관\s*없|제한.*(?:없|해제)|다시\s*포함|제외.*해제)|모든\s*항공사",
            question,
        )
    )
    if updating and not re.search(
        r"상관없|상관\s*없|제한\s*없|해제|풀어|전체|아무|말고", question
    ):
        clears.clear()
        fields = {field for field in fields if extracted[field] is not None}
    if updating and not extracted["exclude_airlines"] and not airline_reset:
        fields.discard("exclude_airlines")
        clears.discard("exclude_airlines")
    elif updating and airline_reset and not extracted["exclude_airlines"]:
        clears.add("exclude_airlines")
    old_values = values.copy()
    for name in fields:
        values[name] = extracted[name]
    defaults = FlightConditions().model_dump(mode="json")
    for name in clears:
        values[name] = defaults[name]
    if reset:
        values = {
            **defaults,
            **{
                key: value
                for key, value in extracted.items()
                if key in plan.changed_fields or value != defaults[key]
            },
        }
        updating = False
    if ("trip_type" in plan.changed_fields and extracted["trip_type"] == "one_way") or re.search(r"왕복\s*말고\s*편도|편도로", question):
        values["trip_type"], values["return_date"] = "one_way", None
    elif re.search(r"왕복|갔다\s*오|돌아오|돌아오는|귀국", question):
        values["trip_type"] = "round_trip"
    if values["trip_type"] == "one_way":
        if (updating and previous.conditions.trip_type == "round_trip" and "trip_type" in fields
                and fields.intersection({"departure", "arrival", "departure_from"})):
            for key in ("date", "departure_from", "departure_to", "arrival_from", "arrival_to"):
                if key not in fields:
                    values[key] = None
        values["return_date"] = None
        values["return_date_from"] = values["return_date_to"] = None
        for key in RETURN_TIME_FIELDS:
            values[key] = None
        if values["sort_by"] == "return_departure_at":
            values["sort_by"] = "departure_at"
        if "departure_from" in fields and extracted["departure_from"] and "date" not in fields:
            values["date"] = None
    elif fields.intersection({"return_date_from", "return_date_to"}) and (
        extracted["return_date_from"] or extracted["return_date_to"]
    ):
        values["return_date"] = None
        if "return_date_from" in fields and "return_date_to" not in fields:
            values["return_date_to"] = None
        for key in RETURN_TIME_FIELDS:
            if key not in fields:
                values[key] = None
    elif "return_date" in fields and extracted["return_date"]:
        values["return_date_from"] = values["return_date_to"] = None
    try:
        _normalize_bare_days(values, fields, question, previous if updating else None)
    except ValueError:
        return clarification("invalid_date")
    if (
        not updating
        and not payload.history
        and not re.search(
            r"싼|싸게|저렴|비싼|비싸|가격순|요금순|빠른|늦은|순서|먼저", question
        )
    ):
        values["sort_by"], values["sort_order"] = "departure_at", "asc"
    _apply_price_bounds(values, question, old_values)
    _apply_calendar(values, question)
    problem = complete_times(values)
    if problem is not None:
        known = {**values, **{key: None for key in TIME_FIELDS}}
        try:
            return clarification(problem, known)
        except ValidationError:
            return clarification("invalid_date")
    if updating:
        problem = shift_times(values, previous, fields, clears)
        if problem is not None:
            return clarification(problem)
    try:
        conditions = FlightConditions.model_validate(values)
    except ValidationError as exc:
        price_error = any(
            error["loc"][0] in ("min_price", "max_price") for error in exc.errors()
        )
        return clarification("invalid_price" if price_error else "invalid_date")
    for prefix, _, _ in TIME_GROUPS:
        lower = getattr(conditions, f"{prefix}_from")
        upper = getattr(conditions, f"{prefix}_to")
        if lower and upper and local_datetime(lower) > local_datetime(upper):
            return clarification("invalid_date")
    for match in explicit_dates(question):
        y, m, d, iy, im, iday = match.groups()
        if y or iy:
            literal = date(int(y or iy), int(m or im), int(d or iday))
            represented = [conditions.date, conditions.return_date, conditions.return_date_from, conditions.return_date_to]
            represented += [
                getattr(conditions, k).date()
                for k in TIME_FIELDS
                if getattr(conditions, k)
            ]
            if represented and literal not in represented and plan.status == "ready":
                return clarification("invalid_date")
    if (
        conditions.min_price is not None
        and conditions.max_price is not None
        and conditions.min_price > conditions.max_price
    ):
        return clarification("invalid_price")
    data = plan.model_dump(exclude={"conditions", "location_sources"})
    data["conditions"] = conditions
    confirm_time = plan.confirm_time or needs_time_confirmation(question, conditions, previous)
    if confirm_time and plan.status != "unsupported" and plan.reason != "local_time" and any(getattr(conditions, key) for key in TIME_FIELDS):
        data.update(status="needs_clarification", reason="time_confirmation", clarification="시간 조건을 확인해 주세요.")
    if (
        updating
        and previous.result_kind == "destinations"
        and not re.search(r"항공편|비행기", question)
    ):
        data["result_kind"] = "destinations"
    elif not re.search(r"공항|목적지", question):
        data["result_kind"] = "flights"
    if updating and plan.max_results is None:
        data["max_results"] = previous.max_results
    return ChatPlan.model_validate(data)


def conditions_have_specific_day(question):
    return bool(re.search(r"[월화수목금토일]요일|\d+\s*일", question))


def _normalize_bare_days(values, fields, question, previous):
    # 월을 생략한 날짜를 모델이 임의로 다음 달로 넘기지 않도록 보정함.
    if re.search(r"\d+\s*[년월]|\d{4}-\d{2}-\d{2}|다음\s*달|다다음\s*달|내년|이번\s*달", question):
        return
    days = {int(day) for day in re.findall(r"(?<!\d)(\d{1,2})\s*일(?![간요일])", question)}
    if not days:
        return
    anchor = (previous.conditions.date if previous else None) or now_local().date()
    for key in fields:
        if key not in {"date", "return_date", "return_date_from", "return_date_to", *TIME_FIELDS}:
            continue
        value = values.get(key)
        if value and len(value) >= 10:
            day = int(value[8:10])
            if day in days:
                values[key] = date(anchor.year, anchor.month, day).isoformat() + value[10:]


def remember(response, plan, payload):
    if plan.dialogue_act == "reset_search":
        response.reset_search = True
        response.context = ChatContext()
        return response
    context = (
        payload.context.model_copy(deep=True) if payload.context else ChatContext()
    )
    context.pending_offer = None
    context.pending_search = None
    context.pending_field = None
    context.pending_options = []
    if response.reason == "time_confirmation":
        context.pending_offer = "confirm_time"
        context.pending_search = SearchSnapshot(
            conditions=plan.conditions.model_copy(deep=True),
            max_results=plan.max_results,
            result_kind=plan.result_kind,
        )
        response.interpreted_conditions = plan.conditions.model_dump(mode="json", exclude_none=True)
        response.context = context
        return response
    if (
        response.reason in ("promotion_period", "discount_calculation")
        and response.status == "needs_clarification"
    ):
        context.pending_offer = "base_price_search"
    elif (
        "flights" in plan.topics
        and response.status == "success"
        and response.count == 0
    ):
        context.pending_offer = "change_search"
    if plan.dialogue_act:
        context.pending_field = None
        context.pending_options = []
    if (
        "flights" in plan.topics
        and plan.status != "unsupported"
        and plan.reason not in ("invalid_date", "invalid_price", "missing_context")
    ):
        snapshot = SearchSnapshot(
            conditions=(
                FlightConditions.model_validate({
                    key: value for key, value in response.interpreted_conditions.items()
                    if key in FlightConditions.model_fields
                })
                if response.status == "success" and response.interpreted_conditions
                else plan.conditions.model_copy(deep=True)
            ),
            max_results=plan.max_results,
            result_kind=plan.result_kind,
        )
        if not context.searches or context.searches[-1] != snapshot:
            context.searches = [*context.searches, snapshot][-5:]
        field = response.clarification.field if response.clarification else None
        context.pending_field = (
            field
            if field in ("departure", "arrival", "date", "return_date", "airline")
            else None
        )
        context.pending_options = (
            [option.value for option in response.clarification.options][:10]
            if response.clarification
            else []
        )
        if not response.interpreted_conditions:
            response.interpreted_conditions = plan.conditions.model_dump(
                mode="json", exclude_none=True
            )
    response.context = context
    return response


def selection_plan(payload):
    if re.fullmatch(
        r"(?:새로운\s*항공편을\s*검색할게요|새\s*검색|새로운\s*검색|처음부터\s*다시\s*검색|검색\s*조건\s*초기화)[.!?\s]*",
        payload.question.strip(),
    ):
        return ChatPlan(status="ready", topics=[], conditions=FlightConditions(), dialogue_act="reset_search")
    context = payload.context
    if context and context.pending_offer == "confirm_time" and context.pending_search:
        value = payload.question.strip()
        if value in ("네", "응", "ㅇㅇ", "예", "맞아", "맞아요", "아니", "아니요"):
            return prepare_dialogue(ChatPlan(
                status="ready", topics=[], conditions=FlightConditions(),
                dialogue_act="decline" if value in ("아니", "아니요") else "accept",
            ), payload)
    if (
        not context
        or context.pending_field not in ("departure", "arrival")
        or not context.searches
    ):
        return None
    value = payload.question.strip().upper()
    options = context.pending_options
    if value in ("네", "응", "ㅇㅇ", "예", "맞아", "맞아요") and len(options) == 1:
        value = options[0]
    elif not re.fullmatch(r"[A-Z]{3,4}", value):
        return None
    # 클라이언트가 전달한 선택값도 실제 공항 조회 단계에서 다시 확인함.
    conditions = context.searches[-1].conditions.model_copy(deep=True)
    setattr(conditions, context.pending_field, value)
    return ChatPlan(
        status="ready",
        topics=["flights"],
        conditions=conditions,
        action="update",
        changed_fields=[context.pending_field],
    )


def _apply_price_bounds(values, question, previous=None):
    for match in re.finditer(
        r"(\d[\d,]*(?:\.\d+)?)\s*(만|천)?\s*원\s*(?:보다\s*)?(이하|미만|밑|아래|이상|초과|비싸)",
        question,
    ):
        amount, unit, operator = match.groups()
        amount = int(
            Decimal(amount.replace(",", "")) * {None: 1, "천": 1000, "만": 10000}[unit]
        )
        upper = operator in ("이하", "미만", "밑", "아래")
        boundary = (
            amount - (operator != "이하") if upper else amount + (operator != "이상")
        )
        excluded = re.match(
            r"(?:인|인\s*항공편|항공편|의\s*항공편)?\s*(?:을|은|는)?\s*(?:제외|빼고)",
            question[match.end() :].lstrip(),
        )
        if excluded:
            original = "max_price" if upper else "min_price"
            if values.get(original) == boundary:
                values[original] = (previous or {}).get(original)
            values["min_price" if upper else "max_price"] = boundary + (
                1 if upper else -1
            )
        elif upper:
            values["max_price"] = boundary
        else:
            values["min_price"] = boundary


def _apply_calendar(values, question):
    periods = calendar_context(now_local().isoformat())
    for pattern, key in (
        (r"다음\s*주(?!\s*(?:[월화수목금토일]요일|말고))", "next_week"),
        (r"이번\s*주말(?!\s*말고)", "this_weekend"),
        (r"다음\s*달(?!\s*말고)", "next_month"),
    ):
        if re.search(pattern, question) and not conditions_have_specific_day(question):
            values["date"] = None
            values["departure_from"] = periods[key]["from"]
            values["departure_to"] = periods[key]["to"]
