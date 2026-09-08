from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Validate the Bearer access token and return the authenticated User.

    Raises HTTP 401 if the token is missing, invalid, expired, or the user
    cannot be found or is inactive.
    """
    _unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Could not validate credentials.",
                "details": {},
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise _unauthorized

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _unauthorized

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise _unauthorized

    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        raise _unauthorized

    user: User | None = db.query(User).filter(User.id == uid).first()
    if user is None:
        raise _unauthorized

    if not user.is_active:
        raise _unauthorized

    return user
