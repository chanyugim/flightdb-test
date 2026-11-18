import re

from app.schemas.chatbot import ChatPlan, FlightConditions
from app.services.chat_policy import REASONS


def prepare_dialogue(plan, payload):
    if not plan.dialogue_act:
        return None
    context = payload.context
    if (
        plan.dialogue_act == "accept"
        and context
        and context.pending_offer == "confirm_time"
        and context.pending_search
    ):
        previous = context.pending_search
        return ChatPlan(
            status="ready", topics=["flights"],
            conditions=previous.conditions.model_copy(deep=True),
            max_results=previous.max_results, result_kind=previous.result_kind,
            action="update", changed_fields=list(FlightConditions.model_fields),
        )
    if (
        plan.dialogue_act == "accept"
        and context
        and context.pending_offer == "base_price_search"
        and context.searches
    ):
        previous = context.searches[-1]
        return ChatPlan(
            status="ready",
            topics=["flights", "promotions"],
            conditions=previous.conditions.model_copy(deep=True),
            max_results=previous.max_results,
            action="update",
            result_kind=previous.result_kind,
        )
    # 대화 응답에 모델이 검색 조건을 함께 넣어도 조회하지 않음.
    return ChatPlan(
        status="ready",
        topics=[],
        conditions=FlightConditions(),
        dialogue_act=plan.dialogue_act,
    )


def dialogue_message(act, context):
    if act == "reset_search":
        return "이전 검색 조건을 지웠어요. 새로 찾을 항공편의 출발지, 목적지나 여행 날짜를 말씀해 주세요. 아직 정하지 않은 조건은 생략해도 괜찮아요."
    if act == "decline":
        return "알겠어요. 추가 검색은 진행하지 않을게요. 필요하시면 원하시는 여행 조건을 말씀해 주세요."
    if act == "acknowledge":
        return "네, 필요하실 때 다시 말씀해 주세요. 여행 준비를 도와드릴게요."
    if act == "accept" and context and context.pending_offer == "change_search":
        return "어떤 조건으로 다시 찾아드릴까요? 원하시는 목적지나 날짜, 가격 조건을 말씀해 주세요."
    return "어떤 내용을 말씀하신 건지 조금 더 알려주시겠어요? 바꾸고 싶은 여행 조건이나 원하시는 안내를 말씀해 주세요."


def normalize_promotion_request(plan, question):
    intent = plan.promotion_request
    reason = plan.reason
    if intent == "current":
        if "flights" in plan.topics and re.search(r"항공편|비행기|왕복|편도|노선", question) and not re.search(r"프로모션|이벤트|할인|혜택|쿠폰|포인트", question):
            return plan.model_copy(update={
                "topics": [topic for topic in plan.topics if topic != "promotions"],
                "promotion_request": None, "promotion_evidence": None,
                "reason": None, "clarification": None, "status": "ready",
            })
        # 목록·사용 방법 안내는 항공편을 다시 조회하지 않음. 명시적인 동시 요청만 유지함.
        flight_request = (
            re.search(r"(?:항공편|비행기|왕복|편도|노선)(?:(?!프로모션|이벤트|할인|혜택|쿠폰).){0,30}(?:찾아|검색|조회|보여|알려)", question)
            or re.search(r"(?:항공편|비행기|노선)(?:과|와|하고|이랑)\s*(?:프로모션|이벤트)", question)
        ) and not re.search(r"(?:프로모션|이벤트|할인|혜택)만|항공편.*(?:말고|제외)", question)
        topics = list(dict.fromkeys([
            *(topic for topic in plan.topics if topic != "flights" or flight_request),
            "promotions",
        ]))
        return plan.model_copy(update={
            "topics": topics, "status": "ready", "reason": None,
            "clarification": None, "dialogue_act": None, "confirm_time": False,
        })
    if reason not in (
        None,
        "multiple_promotions",
        "discount_calculation",
        "promotion_period",
    ):
        return plan
    if (
        (
            intent in ("travel_period", "discounted_price", "stacking")
            or reason is not None
        )
        and "flights" in plan.topics
        and re.search(r"항공편|비행기|노선", question)
        and not re.search(
            r"이벤트|프로모션|할인|쿠폰|포인트|혜택|그\s*(?:기간|조건|중|때)|해당\s*기간",
            question,
        )
    ):
        # 과거의 미지원 사유를 새로운 일반 항공편 요청에 재적용하지 않음.
        return plan.model_copy(
            update={
                "status": "ready",
                "reason": None,
                "clarification": None,
                "promotion_request": None,
                "promotion_evidence": None,
                "topics": [topic for topic in plan.topics if topic != "promotions"],
            }
        )
    if reason == "multiple_promotions" or intent == "stacking":
        evidence = plan.promotion_evidence or ""
        explicit = evidence in question and re.search(
            r"중복\s*(?:할인|적용)|(?:동시에|함께|합산|겹쳐|모두|둘\s*다).{0,12}(?:적용|할인)|(?:할인|프로모션|쿠폰).{0,12}(?:합쳐|합산)",
            evidence,
        )
        if explicit:
            return plan.model_copy(
                update={
                    "status": "unsupported",
                    "reason": "multiple_promotions",
                    "dialogue_act": None,
                }
            )
        # 중복 적용의 원문 근거가 없으면 해당 사유로 단정하지 않음.
        intent = "travel_period"
    if intent == "travel_period" or reason == "promotion_period":
        reason = "promotion_period"
    elif intent == "discounted_price" or reason == "discount_calculation":
        reason = "discount_calculation"
    else:
        return plan
    topics = list(dict.fromkeys([*plan.topics, "flights", "promotions"]))
    return plan.model_copy(
        update={
            "status": "needs_clarification",
            "reason": reason,
            "clarification": REASONS[reason],
            "topics": topics,
        }
    )
