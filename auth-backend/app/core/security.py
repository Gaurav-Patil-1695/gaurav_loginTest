from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config.settings import settings


# ---------------------------------------------------------------------------
# Password hashing (bcrypt)
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*."""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return *True* if *plain_password* matches *password_hash*."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# Token hashing (SHA-256)
# ---------------------------------------------------------------------------

def hash_token(token: str) -> str:
    """Return the hex-encoded SHA-256 digest of *token*.

    Refresh tokens and password-reset tokens are stored hashed so that a
    database breach does not expose usable tokens (NFR-02, NFR-04).
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode a signed JWT access token.

    Args:
        subject: Value placed in the ``sub`` claim (typically the user id).
        extra_claims: Optional additional claims merged into the payload.
        expires_delta: Override the default expiry from settings.

    Returns:
        A signed JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode a signed JWT refresh token.

    Args:
        subject: Value placed in the ``sub`` claim (typically the user id).
        extra_claims: Optional additional claims merged into the payload.
        expires_delta: Override the default expiry from settings.

    Returns:
        A signed JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token.

    Args:
        token: The raw JWT string.

    Returns:
        The decoded payload as a plain dictionary.

    Raises:
        :class:`jose.JWTError`: If the token is invalid, expired, or the
            signature cannot be verified.
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Additionally asserts that the ``type`` claim equals ``"access"``.

    Raises:
        :class:`jose.JWTError`: If the token is invalid or has the wrong type.
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Token type is not 'access'")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT refresh token.

    Additionally asserts that the ``type`` claim equals ``"refresh"``.

    Raises:
        :class:`jose.JWTError`: If the token is invalid or has the wrong type.
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Token type is not 'refresh'")
    return payload
