from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()
password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummy-password-for-timing-check")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def verify_password_or_dummy(
    plain_password: str,
    hashed_password: str | None,
) -> bool:
    target_hash = hashed_password or DUMMY_HASH
    return verify_password(plain_password, target_hash)


def create_access_token(
    member_id: str,
    role_type: str,
) -> tuple[str, int]:
    expires_minutes = settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)

    payload = {
        "sub": member_id,
        "role": role_type,
        "type": "access",
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_minutes * 60


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat"]},
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc

    if payload.get("type") != "access":
        raise ValueError("Invalid token type")

    if not payload.get("sub"):
        raise ValueError("Missing subject")

    return payload
