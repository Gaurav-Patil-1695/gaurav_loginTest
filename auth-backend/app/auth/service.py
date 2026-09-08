import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, Request, Response, status
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
REFRESH_TOKEN_REMEMBER_DAYS: int = int(os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
RESET_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_COOKIE_NAME: str = "refresh_token"

# ---------------------------------------------------------------------------
# In-memory stores (replace with real DB repositories in production)
# ---------------------------------------------------------------------------
_users: dict[str, dict] = {}          # email -> user record
_users_by_id: dict[str, dict] = {}    # id -> user record
_password_resets: list[dict] = []     # list of password_reset records
_refresh_tokens: list[dict] = []      # list of refresh_token records


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def _set_refresh_cookie(response: Response, token: str, remember: bool) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_DAYS * 86400 if remember else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=max_age,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/auth/refresh")


class AuthService:
    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------
    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = _users.get(body.email)
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
        if not user or not _verify_password(body.password, user["password_hash"]):
            raise invalid_exc
        if not user["is_active"]:
            raise invalid_exc

        access_token = _create_access_token(user["id"], user["email"])
        raw_refresh = _create_refresh_token()
        remember = getattr(body, "remember_me", False) or False
        expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)
        _refresh_tokens.append(
            {
                "id": secrets.token_hex(16),
                "user_id": user["id"],
                "token_hash": _sha256(raw_refresh),
                "expires_at": expires_at,
                "revoked_at": None,
                "remember_me": remember,
                "created_at": datetime.now(timezone.utc),
            }
        )
        _set_refresh_cookie(response, raw_refresh, remember)
        return LoginResponse(
            accessToken=access_token,
            tokenType="bearer",
            user={
                "id": user["id"],
                "fullName": user["full_name"],
                "email": user["email"],
            },
        )

    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        if body.password != body.confirmPassword:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PASSWORD_MISMATCH",
                        "message": "Passwords do not match.",
                        "details": {"field": "confirmPassword"},
                    }
                },
            )
        if body.email in _users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": {"field": "email"},
                    }
                },
            )
        user_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        user = {
            "id": user_id,
            "full_name": body.fullName,
            "email": body.email,
            "password_hash": _hash_password(body.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        _users[body.email] = user
        _users_by_id[user_id] = user
        return RegisterResponse(
            message="Account created successfully.",
            user={
                "id": user_id,
                "fullName": body.fullName,
                "email": body.email,
            },
        )

    # ------------------------------------------------------------------
    # forgotPassword
    # ------------------------------------------------------------------
    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        # Enumeration-resistant: always return the same response
        user = _users.get(body.email)
        if user and user["is_active"]:
            raw_token = secrets.token_urlsafe(32)
            token_hash = _sha256(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
            _password_resets.append(
                {
                    "id": secrets.token_hex(16),
                    "user_id": user["id"],
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                    "used_at": None,
                    "created_at": datetime.now(timezone.utc),
                }
            )
            # In production: send email with raw_token link here
        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    # ------------------------------------------------------------------
    # resetPassword
    # ------------------------------------------------------------------
    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        if body.password != body.confirmPassword:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PASSWORD_MISMATCH",
                        "message": "Passwords do not match.",
                        "details": {"field": "confirmPassword"},
                    }
                },
            )

        token_hash = _sha256(body.token)
        now = datetime.now(timezone.utc)

        reset_record: Optional[dict] = None
        for record in _password_resets:
            if (
                record["token_hash"] == token_hash
                and record["used_at"] is None
                and record["expires_at"] > now
            ):
                reset_record = record
                break

        if reset_record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_OR_EXPIRED_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": {},
                    }
                },
            )

        user = _users_by_id.get(reset_record["user_id"])
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_OR_EXPIRED_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": {},
                    }
                },
            )

        # Mark token as used
        reset_record["used_at"] = now

        # Update password
        new_hash = _hash_password(body.password)
        user["password_hash"] = new_hash
        user["updated_at"] = now

        # Revoke all refresh tokens for this user
        for rt in _refresh_tokens:
            if rt["user_id"] == user["id"] and rt["revoked_at"] is None:
                rt["revoked_at"] = now

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    # ------------------------------------------------------------------
    # me
    # ------------------------------------------------------------------
    async def me(self) -> MeResponse:
        # Placeholder: token extraction from request would be done via Depends in production
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

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------
    async def logout(self, request: Request, response: Response) -> LogoutResponse:
        raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
        if raw_refresh:
            token_hash = _sha256(raw_refresh)
            now = datetime.now(timezone.utc)
            for rt in _refresh_tokens:
                if rt["token_hash"] == token_hash and rt["revoked_at"] is None:
                    rt["revoked_at"] = now
                    break
        _clear_refresh_cookie(response)
        return LogoutResponse(message="Logged out successfully.")

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------
    async def refresh(self, request: Request, response: Response) -> RefreshResponse:
        raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
        if not raw_refresh:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "MISSING_REFRESH_TOKEN",
                        "message": "Refresh token is missing.",
                        "details": {},
                    }
                },
            )
        token_hash = _sha256(raw_refresh)
        now = datetime.now(timezone.utc)
        rt_record: Optional[dict] = None
        for rt in _refresh_tokens:
            if (
                rt["token_hash"] == token_hash
                and rt["revoked_at"] is None
                and rt["expires_at"] > now
            ):
                rt_record = rt
                break

        if rt_record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Refresh token is invalid or expired.",
                        "details": {},
                    }
                },
            )

        # Rotate: revoke old, issue new
        rt_record["revoked_at"] = now
        user = _users_by_id.get(rt_record["user_id"])
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Refresh token is invalid or expired.",
                        "details": {},
                    }
                },
            )

        access_token = _create_access_token(user["id"], user["email"])
        new_raw_refresh = _create_refresh_token()
        remember = rt_record.get("remember_me", False)
        expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        new_expires_at = now + timedelta(days=expire_days)
        _refresh_tokens.append(
            {
                "id": secrets.token_hex(16),
                "user_id": user["id"],
                "token_hash": _sha256(new_raw_refresh),
                "expires_at": new_expires_at,
                "revoked_at": None,
                "remember_me": remember,
                "created_at": now,
            }
        )
        _set_refresh_cookie(response, new_raw_refresh, remember)
        return RefreshResponse(accessToken=access_token, tokenType="bearer")
