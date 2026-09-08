from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config.settings import settings

# ---------------------------------------------------------------------------
# TTL constants
# ---------------------------------------------------------------------------

ACCESS_TOKEN_TTL: timedelta = timedelta(
    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)

# Standard refresh TTL (no rememberMe)
REFRESH_TOKEN_TTL: timedelta = timedelta(
    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
)

# Extended refresh TTL when rememberMe=True
REFRESH_TOKEN_EXTENDED_TTL: timedelta = timedelta(
    days=settings.REFRESH_TOKEN_REMEMBER_ME_EXPIRE_DAYS
)

RESET_TOKEN_TTL: timedelta = timedelta(
    minutes=settings.RESET_TOKEN_EXPIRE_MINUTES
)


# ---------------------------------------------------------------------------
# Raw token generation
# ---------------------------------------------------------------------------

def _generate_raw_token(nbytes: int = 32) -> str:
    """Return a URL-safe random token string."""
    return secrets.token_urlsafe(nbytes)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def hash_token(raw_token: str) -> str:
    """SHA-256 hash a raw token for safe storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Access token (JWT)
# ---------------------------------------------------------------------------

def create_access_token(
    user_id: int,
    email: str,
    extra_claims: dict | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Payload:
        sub  - str(user_id)
        email
        iat  - issued-at (UTC)
        exp  - expiry (UTC)
        + any extra_claims
    """
    now = datetime.now(tz=timezone.utc)
    exp = now + ACCESS_TOKEN_TTL

    payload: dict = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": exp,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Raises:
        jose.JWTError on invalid / expired tokens.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


# ---------------------------------------------------------------------------
# Refresh token (opaque)
# ---------------------------------------------------------------------------

def create_refresh_token(remember_me: bool = False) -> tuple[str, str, datetime]:
    """
    Generate an opaque refresh token.

    Returns:
        (raw_token, token_hash, expires_at)

    The caller is responsible for persisting token_hash + expires_at.
    TTL is extended when remember_me=True.
    """
    raw = _generate_raw_token()
    token_hash = hash_token(raw)
    ttl = REFRESH_TOKEN_EXTENDED_TTL if remember_me else REFRESH_TOKEN_TTL
    expires_at = datetime.now(tz=timezone.utc) + ttl
    return raw, token_hash, expires_at


def is_refresh_token_valid(token_row: dict) -> bool:
    """
    Return True when the refresh token row from the DB is still usable.

    Checks:
        - not revoked (revoked_at IS NULL)
        - not expired (expires_at > now)
    """
    if token_row.get("revoked_at") is not None:
        return False
    expires_at: datetime = token_row["expires_at"]
    # Make timezone-aware for comparison if the DB returns naive datetimes
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Password reset token (opaque)
# ---------------------------------------------------------------------------

def create_reset_token() -> tuple[str, str, datetime]:
    """
    Generate an opaque password-reset token.

    Returns:
        (raw_token, token_hash, expires_at)

    The caller is responsible for persisting token_hash + expires_at.
    """
    raw = _generate_raw_token()
    token_hash = hash_token(raw)
    expires_at = datetime.now(tz=timezone.utc) + RESET_TOKEN_TTL
    return raw, token_hash, expires_at


def is_reset_token_valid(reset_row: dict) -> bool:
    """
    Return True when the password_reset row from the DB is still usable.

    Checks:
        - not already used (used_at IS NULL)
        - not expired (expires_at > now)
    """
    if reset_row.get("used_at") is not None:
        return False
    expires_at: datetime = reset_row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Token rotation helper (thin wrapper, DB calls handled by repository)
# ---------------------------------------------------------------------------

def build_rotated_refresh_token(
    remember_me: bool,
) -> tuple[str, str, datetime]:
    """
    Produce a replacement refresh token during rotation.

    Returns:
        (new_raw_token, new_token_hash, new_expires_at)

    The caller must persist the new token and revoke the old one via the
    repository (repository.rotate_refresh_token).
    """
    return create_refresh_token(remember_me=remember_me)


# ---------------------------------------------------------------------------
# Revocation helpers (thin wrappers kept here for symmetry; actual DB writes
# are performed in repository.py)
# ---------------------------------------------------------------------------

def make_token_hash(raw_token: str) -> str:
    """Convenience alias — hash an incoming raw token before DB lookup."""
    return hash_token(raw_token)
