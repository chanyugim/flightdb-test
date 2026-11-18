from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limit_sensitive_requests
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password_or_dummy,
)
from app.models.member_account import MemberAccount
from app.models.member_grade import MemberGrade
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.member import MemberResponse
from app.services.members import member_to_dict

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_sensitive_requests)],
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    if db.get(MemberAccount, payload.member_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="동일 아이디가 이미 존재합니다.",
        )

    basic_grade = db.get(MemberGrade, "BASIC")
    if basic_grade is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="BASIC 등급 설정이 되지 않았습니다.",
        )

    member = MemberAccount(
        member_id=payload.member_id,
        grade_code="BASIC",
        password_hash=hash_password(payload.password),
        name=payload.name,
        birth_date=payload.birth_date,
        gender=payload.gender.upper(),
        phone=payload.phone,
        point_balance=0,
        role_type="일반",
    )

    db.add(member)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if db.get(MemberAccount, payload.member_id) is not None:
            raise HTTPException(
                status_code=409, detail="동일 아이디가 이미 존재합니다."
            ) from exc
        raise
    db.refresh(member)

    return member_to_dict(member, basic_grade)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(limit_sensitive_requests)],
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    member = db.get(MemberAccount, payload.member_id)

    password_ok = verify_password_or_dummy(
        payload.password,
        member.password_hash if member else None,
    )

    if member is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 틀렸습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = create_access_token(
        member_id=member.member_id,
        role_type=member.role_type,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }
