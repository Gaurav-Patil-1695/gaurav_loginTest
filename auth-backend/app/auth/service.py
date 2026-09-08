import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))

# ---------------------------------------------------------------------------
# In-memory stores — replace with real DB repositories in production
# ---------------------------------------------------------------------------
_users: dict[str, dict] = {}  # keyed by email
_users_by_id: dict[str, dict] = {}  # keyed by id
_password_resets: dict[str, dict] = {}  # keyed by token_hash
_refresh_tokens: dict[str, dict] = {}  # keyed by token_hash


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _make_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _make_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def _new_id() -> str:
    return secrets.token_hex(16)


def _validate_password_policy(password: str) -> Optional[str]:
    """Return an error message if policy is violated, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    return None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AuthService:
    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        # Normalise email
        email = payload.email.strip().lower()

        # Duplicate-email check
        if email in _users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": {},
                    }
                },
            )

        # Password policy
        policy_error = _validate_password_policy(payload.password)
        if policy_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "WEAK_PASSWORD",
                        "message": policy_error,
                        "details": {},
                    }
                },
            )

        # Confirm password match
        if payload.password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PASSWORD_MISMATCH",
                        "message": "Passwords do not match.",
                        "details": {},
                    }
                },
            )

        # Persist user
        user_id = _new_id()
        now = datetime.now(timezone.utc)
        user: dict = {
            "id": user_id,
            "full_name": payload.full_name.strip(),
            "email": email,
            "password_hash": _hash_password(payload.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        _users[email] = user
        _users_by_id[user_id] = user

        # Issue tokens
        access_token = _make_access_token(user_id, email)
        raw_refresh = _make_refresh_token()
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        _refresh_tokens[_sha256(raw_refresh)] = {
            "id": _new_id(),
            "user_id": user_id,
            "token_hash": _sha256(raw_refresh),
            "expires_at": refresh_expires,
            "revoked_at": None,
            "remember_me": False,
            "created_at": now,
        }

        return RegisterResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            user={
                "id": user_id,
                "full_name": user["full_name"],
                "email": email,
            },
        )

    async def login(self, payload: LoginRequest) -> LoginResponse:
        email = payload.email.strip().lower()
        user = _users.get(email)
        invalid_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": {},
                }
            },
        )
        if user is None:
            raise invalid_exc
        if not _verify_password(payload.password, user["password_hash"]):
            raise invalid_exc
        if not user["is_active"]:
            raise invalid_exc

        access_token = _make_access_token(user["id"], email)
        raw_refresh = _make_refresh_token()
        now = datetime.now(timezone.utc)
        remember = getattr(payload, "remember_me", False) or False
        days = REFRESH_TOKEN_EXPIRE_DAYS * (30 if remember else 1)
        refresh_expires = now + timedelta(days=days)
        _refresh_tokens[_sha256(raw_refresh)] = {
            "id": _new_id(),
            "user_id": user["id"],
            "token_hash": _sha256(raw_refresh),
            "expires_at": refresh_expires,
            "revoked_at": None,
            "remember_me": remember,
            "created_at": now,
        }

        return LoginResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            user={
                "id": user["id"],
                "full_name": user["full_name"],
                "email": email,
            },
        )

    async def forgotPassword(self, payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
        # Enumeration-resistant: always return the same response
        email = payload.email.strip().lower()
        user = _users.get(email)
        if user is not None and user["is_active"]:
            raw_token = secrets.token_urlsafe(32)
            token_hash = _sha256(raw_token)
            now = datetime.now(timezone.utc)
            _password_resets[token_hash] = {
                "id": _new_id(),
                "user_id": user["id"],
                "token_hash": token_hash,
                "expires_at": now + timedelta(hours=1),
                "used_at": None,
                "created_at": now,
            }
            # In production: send email with raw_token

        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    async def resetPassword(self, payload: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _sha256(payload.token)
        record = _password_resets.get(token_hash)
        invalid_exc = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_RESET_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": {},
                }
            },
        )
        if record is None:
            raise invalid_exc
        if record["used_at"] is not None:
            raise invalid_exc
        if record["expires_at"] < datetime.now(timezone.utc):
            raise invalid_exc

        if payload.password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PASSWORD_MISMATCH",
                        "message": "Passwords do not match.",
                        "details": {},
                    }
                },
            )

        policy_error = _validate_password_policy(payload.password)
        if policy_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "WEAK_PASSWORD",
                        "message": policy_error,
                        "details": {},
                    }
                },
            )

        user = _users_by_id.get(record["user_id"])
        if user is None:
            raise invalid_exc

        user["password_hash"] = _hash_password(payload.password)
        user["updated_at"] = datetime.now(timezone.utc)
        record["used_at"] = datetime.now(timezone.utc)

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self) -> MeResponse:
        # Placeholder — real implementation decodes Authorization header
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required.",
                    "details": {},
                }
            },
        )

    async def logout(self) -> LogoutResponse:
        # Placeholder — real implementation revokes the refresh token
        return LogoutResponse(message="Logged out successfully.")

    async def refresh(self) -> RefreshResponse:
        # Placeholder — real implementation validates & rotates the refresh token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": {},
                }
            },
        )
