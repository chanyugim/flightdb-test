from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.member_account import MemberAccount

bearer_scheme = HTTPBearer(auto_error=False)


def _member_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
    authorization_header: str | None = None,
) -> MemberAccount | None:
    if credentials is None:
        if authorization_header is not None:
            raise HTTPException(
                401,
                "Invalid authentication header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    member = db.get(MemberAccount, payload["sub"])

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Member not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return member


def get_optional_current_member(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> MemberAccount | None:
    return _member_from_credentials(
        credentials, db, request.headers.get("authorization")
    )


def get_current_member(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> MemberAccount:
    member = _member_from_credentials(
        credentials, db, request.headers.get("authorization")
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return member


def require_admin(
    current_member: MemberAccount = Depends(get_current_member),
) -> MemberAccount:
    if current_member.role_type != "관리자":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission required",
        )

    return current_member
