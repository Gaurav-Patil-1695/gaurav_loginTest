from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Response, status

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

# ---------------------------------------------------------------------------
# Environment / configuration
# ---------------------------------------------------------------------------
JWT_SECRET: str = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)
REFRESH_TOKEN_REMEMBER_ME_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_REMEMBER_ME_DAYS", "30")
)
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
COOKIE_NAME: str = "refresh_token"

# ---------------------------------------------------------------------------
# In-memory stores (replace with real DB repositories in production)
# ---------------------------------------------------------------------------
# users: {email: {id, full_name, email, password_hash, is_active, created_at, updated_at}}
_users: dict[str, dict] = {}
# refresh_tokens: {token_hash: {id, user_id, token_hash, expires_at, revoked_at, remember_me, created_at}}
_refresh_tokens: dict[str, dict] = {}
# revoked access tokens (jti set)
_revoked_access_jtis: set[str] = set()
# password_resets: {token_hash: {id, user_id, token_hash, expires_at, used_at, created_at}}
_password_resets: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _make_access_token(user_id: str, email: str) -> tuple[str, str]:
    """Return (token, jti)."""
    jti = secrets.token_hex(16)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, jti


def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )
    return payload


def _make_refresh_token(
    user_id: str,
    remember_me: bool,
) -> tuple[str, str, datetime]:
    """Return (raw_token, token_hash, expires_at)."""
    raw = secrets.token_urlsafe(48)
    token_hash = _sha256(raw)
    days = REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    record_id = secrets.token_hex(16)
    _refresh_tokens[token_hash] = {
        "id": record_id,
        "user_id": user_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
        "revoked_at": None,
        "remember_me": remember_me,
        "created_at": datetime.now(timezone.utc),
    }
    return raw, token_hash, expires_at


def _set_refresh_cookie(response: Response, raw_token: str, expires_at: datetime) -> None:
    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=max_age,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/auth/refresh",
        httponly=True,
        samesite="lax",
        secure=True,
    )


def _validate_password_strength(password: str) -> Optional[str]:
    """Return an error message or None if password is valid."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    return None


def _get_user_by_email(email: str) -> Optional[dict]:
    return _users.get(email.lower())


def _get_user_by_id(user_id: str) -> Optional[dict]:
    for u in _users.values():
        if u["id"] == user_id:
            return u
    return None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AuthService:
    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        email = body.email.lower()

        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Passwords do not match.",
                        "details": [{"field": "confirmPassword", "message": "Passwords do not match."}],
                    }
                },
            )

        pw_error = _validate_password_strength(body.password)
        if pw_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": pw_error,
                        "details": [{"field": "password", "message": pw_error}],
                    }
                },
            )

        if _get_user_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": [{"field": "email", "message": "An account with this email already exists."}],
                    }
                },
            )

        user_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        _users[email] = {
            "id": user_id,
            "full_name": body.full_name,
            "email": email,
            "password_hash": _hash_password(body.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        return RegisterResponse(
            message="Account created successfully.",
            user_id=user_id,
        )

    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------
    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        email = body.email.lower()
        user = _get_user_by_email(email)
        invalid = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": [],
                }
            },
        )

        if user is None or not _verify_password(body.password, user["password_hash"]):
            raise invalid

        if not user["is_active"]:
            raise invalid

        remember_me: bool = body.remember_me if body.remember_me is not None else False
        access_token, _jti = _make_access_token(user["id"], user["email"])
        raw_refresh, _rh, expires_at = _make_refresh_token(user["id"], remember_me)
        _set_refresh_cookie(response, raw_refresh, expires_at)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # forgotPassword
    # ------------------------------------------------------------------
    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        # Enumeration resistance: always return the same response
        email = body.email.lower()
        user = _get_user_by_email(email)
        if user is not None and user["is_active"]:
            raw_token = secrets.token_urlsafe(32)
            token_hash = _sha256(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            record_id = secrets.token_hex(16)
            _password_resets[token_hash] = {
                "id": record_id,
                "user_id": user["id"],
                "token_hash": token_hash,
                "expires_at": expires_at,
                "used_at": None,
                "created_at": datetime.now(timezone.utc),
            }
            # In production: send email with raw_token

        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    # ------------------------------------------------------------------
    # resetPassword
    # ------------------------------------------------------------------
    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _sha256(body.token)
        reset_record = _password_resets.get(token_hash)

        invalid_token_exc = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_RESET_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": [],
                }
            },
        )

        if reset_record is None:
            raise invalid_token_exc
        if reset_record["used_at"] is not None:
            raise invalid_token_exc
        if datetime.now(timezone.utc) > reset_record["expires_at"]:
            raise invalid_token_exc

        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Passwords do not match.",
                        "details": [{"field": "confirmPassword", "message": "Passwords do not match."}],
                    }
                },
            )

        pw_error = _validate_password_strength(body.password)
        if pw_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": pw_error,
                        "details": [{"field": "password", "message": pw_error}],
                    }
                },
            )

        user = _get_user_by_id(reset_record["user_id"])
        if user is None:
            raise invalid_token_exc

        user["password_hash"] = _hash_password(body.password)
        user["updated_at"] = datetime.now(timezone.utc)
        reset_record["used_at"] = datetime.now(timezone.utc)

        # Revoke all existing refresh tokens for this user
        for rt in _refresh_tokens.values():
            if rt["user_id"] == user["id"] and rt["revoked_at"] is None:
                rt["revoked_at"] = datetime.now(timezone.utc)

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    # ------------------------------------------------------------------
    # me
    # ------------------------------------------------------------------
    async def me(self, access_token: str) -> MeResponse:
        payload = _decode_access_token(access_token)
        jti: str = payload.get("jti", "")
        if jti in _revoked_access_jtis:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked.",
            )
        user_id: str = payload.get("sub", "")
        user = _get_user_by_id(user_id)
        if user is None or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        return MeResponse(
            id=user["id"],
            full_name=user["full_name"],
            email=user["email"],
            is_active=user["is_active"],
            created_at=user["created_at"],
        )

    # ------------------------------------------------------------------
    # logout  (FR-06)
    # ------------------------------------------------------------------
    async def logout(
        self,
        body: LogoutRequest,
        access_token: Optional[str],
        response: Response,
    ) -> LogoutResponse:
        # Revoke the access token by its jti if present and valid
        if access_token:
            try:
                payload = _decode_access_token(access_token)
                jti: str = payload.get("jti", "")
                if jti:
                    _revoked_access_jtis.add(jti)
            except HTTPException:
                # Already expired or invalid — treat as acceptable during logout
                pass

        # Revoke the refresh token if provided in the request body
        if body.refresh_token:
            token_hash = _sha256(body.refresh_token)
            rt_record = _refresh_tokens.get(token_hash)
            if rt_record is not None and rt_record["revoked_at"] is None:
                rt_record["revoked_at"] = datetime.now(timezone.utc)

        # Clear the refresh token cookie
        _clear_refresh_cookie(response)

        return LogoutResponse(message="You have been logged out successfully.")

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------
    async def refresh(self, body: RefreshRequest, response: Response) -> RefreshResponse:
        raw_token: Optional[str] = body.refresh_token
        if not raw_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Refresh token is missing.",
                        "details": [],
                    }
                },
            )

        token_hash = _sha256(raw_token)
        rt_record = _refresh_tokens.get(token_hash)

        invalid_rt_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": [],
                }
            },
        )

        if rt_record is None:
            raise invalid_rt_exc
        if rt_record["revoked_at"] is not None:
            raise invalid_rt_exc
        if datetime.now(timezone.utc) > rt_record["expires_at"]:
            raise invalid_rt_exc

        user_id: str = rt_record["user_id"]
        user = _get_user_by_id(user_id)
        if user is None or not user["is_active"]:
            raise invalid_rt_exc

        # Rotate: revoke old, issue new
        rt_record["revoked_at"] = datetime.now(timezone.utc)
        remember_me: bool = rt_record["remember_me"]

        new_access_token, _jti = _make_access_token(user["id"], user["email"])
        raw_new_refresh, _rh, expires_at = _make_refresh_token(user["id"], remember_me)
        _set_refresh_cookie(response, raw_new_refresh, expires_at)

        return RefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
