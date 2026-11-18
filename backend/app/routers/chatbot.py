from threading import BoundedSemaphore
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.database import get_chat_db, start_chat_read_only
from app.core.dependencies import bearer_scheme, _member_from_credentials
from app.core.rate_limit import RequestLimiter
from app.core.time import KST, now_local
from app.integrations.gemini import GeminiError, generate_plan
from app.schemas.chatbot import ChatPlan, ChatRequest, ChatResponse, FlightConditions
from app.services.chatbot import answer_plan
from app.services.chat_context import selection_plan
from app.services.chat_policy import guard_question, REASONS

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


limiter = RequestLimiter()
slots = BoundedSemaphore(8)


@router.post("/messages", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    db: Annotated[Session, Depends(get_chat_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
):
    settings = get_settings()
    request_id = str(uuid4())

    def failure(status_code, code, detail):
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail, "code": code, "request_id": request_id},
            headers={"Retry-After": "60"} if status_code == 429 else None,
        )

    if (
        not settings.chatbot_enabled
        or not settings.gemini_api_key.get_secret_value().strip()
    ):
        return failure(
            503,
            "CHATBOT_DISABLED",
            "지금은 챗봇 상담이 준비되어 있지 않아요. 일반 검색을 이용해 주세요.",
        )
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client, settings.chatbot_requests_per_minute):
        return failure(
            429,
            "CHATBOT_RATE_LIMITED",
            "요청이 잠시 몰렸어요. 조금 뒤에 다시 말씀해 주세요.",
        )
    if not slots.acquire(blocking=False):
        return failure(
            429,
            "CHATBOT_RATE_LIMITED",
            "지금 검색 요청이 몰리고 있어요. 잠시 후 다시 시도해 주세요.",
        )
    try:
        reason = guard_question(payload.question)
        if reason:
            plan = ChatPlan(
                status="needs_clarification"
                if reason == "invalid_date"
                else "unsupported",
                topics=[],
                conditions=FlightConditions(),
                reason=reason,
                clarification=REASONS[reason],
            )
        elif (selected := selection_plan(payload)) is not None:
            plan = selected
        else:
            plan = await generate_plan(
                payload.question,
                now_local().replace(tzinfo=KST).isoformat(),
                settings,
                history=payload.history,
                context=payload.context,
            )
        return await run_in_threadpool(
            _answer_authenticated,
            db,
            plan,
            payload,
            request_id,
            credentials,
            request.headers.get("authorization"),
        )
    except GeminiError as exc:
        return failure(exc.status_code, exc.code, exc.message)
    except SQLAlchemyError:
        await run_in_threadpool(db.rollback)
        return failure(
            503,
            "CHATBOT_DATABASE_UNAVAILABLE",
            "지금은 정보를 조회하기 어려워요. 잠시 후 다시 찾아드릴게요.",
        )
    finally:
        slots.release()


def _answer_authenticated(db, plan, payload, request_id, credentials, authorization):
    if credentials is not None:
        start_chat_read_only(db)
    member = _member_from_credentials(credentials, db, authorization)
    return answer_plan(db, plan, payload, request_id, current_member=member)
