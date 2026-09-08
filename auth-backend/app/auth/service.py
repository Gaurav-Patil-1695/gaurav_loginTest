import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

# ---------------------------------------------------------------------------
# Environment / configuration helpers
# ---------------------------------------------------------------------------

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


JWT_SECRET: str = _env("JWT_SECRET", "changeme")
JWT_ALGORITHM: str = _env("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_env("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(_env("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REMEMBER_ME_EXPIRE_DAYS: int = int(_env("REMEMBER_ME_EXPIRE_DAYS", "30"))
RESET_TOKEN_EXPIRE_MINUTES: int = int(_env("RESET_TOKEN_EXPIRE_MINUTES", "60"))
BCRYPT_ROUNDS: int = int(_env("BCRYPT_ROUNDS", "12"))
FRONTEND_URL: str = _env("FRONTEND_URL", "http://localhost:3000")

# ---------------------------------------------------------------------------
# In-memory stores (replace with real DB repositories in production)
# ---------------------------------------------------------------------------

# users: dict keyed by email -> User record dict
_users: dict[str, dict] = {}
# password_resets: list of reset record dicts
_password_resets: list[dict] = []
# refresh_tokens: list of refresh token record dicts
_refresh_tokens: list[dict] = []

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_access_token(user_id: str, email: str) -> str:
    expire = _now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": _now(),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _make_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Invalid token."},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Token has expired."},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid token."},
        )


def _validate_password_strength(password: str) -> Optional[str]:
    """Returns an error message if the password fails policy, else None."""
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
# AuthService
# ---------------------------------------------------------------------------

class AuthService:
    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        # Duplicate email check
        if body.email in _users:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "EMAIL_TAKEN",
                    "message": "An account with this email already exists.",
                    "details": {"field": "email"},
                },
            )

        # Password strength
        pw_error = _validate_password_strength(body.password)
        if pw_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "WEAK_PASSWORD",
                    "message": pw_error,
                    "details": {"field": "password"},
                },
            )

        # Confirm password
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PASSWORD_MISMATCH",
                    "message": "Passwords do not match.",
                    "details": {"field": "confirm_password"},
                },
            )

        user_id = secrets.token_hex(16)
        now = _now()
        user = {
            "id": user_id,
            "full_name": body.full_name,
            "email": body.email,
            "password_hash": _hash_password(body.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        _users[body.email] = user

        return RegisterResponse(
            id=user_id,
            fullName=body.full_name,
            email=body.email,
        )

    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------
    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = _users.get(body.email)
        invalid_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
            },
        )

        if user is None:
            raise invalid_exc
        if not _verify_password(body.password, user["password_hash"]):
            raise invalid_exc
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ACCOUNT_INACTIVE",
                    "message": "Your account is inactive.",
                },
            )

        access_token = _make_access_token(user["id"], user["email"])
        raw_refresh = _make_refresh_token()
        remember = body.remember_me if body.remember_me is not None else False
        expire_days = REMEMBER_ME_EXPIRE_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        rt_expires = _now() + timedelta(days=expire_days)

        _refresh_tokens.append(
            {
                "id": secrets.token_hex(16),
                "user_id": user["id"],
                "token_hash": _sha256(raw_refresh),
                "expires_at": rt_expires,
                "revoked_at": None,
                "remember_me": remember,
                "created_at": _now(),
            }
        )

        response.set_cookie(
            key="refresh_token",
            value=raw_refresh,
            httponly=True,
            samesite="lax",
            secure=True,
            max_age=int(timedelta(days=expire_days).total_seconds()),
            path="/auth/refresh",
        )

        return LoginResponse(
            accessToken=access_token,
            tokenType="bearer",
        )

    # ------------------------------------------------------------------
    # forgotPassword
    # ------------------------------------------------------------------
    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        """
        Enumeration-resistant: always returns 202 with the same message
        regardless of whether the email is registered (NFR-03).
        """
        _GENERIC_MESSAGE = (
            "If an account with that email exists, "
            "a password reset link has been sent."
        )

        user = _users.get(body.email)
        if user is not None and user["is_active"]:
            raw_token = secrets.token_urlsafe(32)
            token_hash = _sha256(raw_token)
            expires_at = _now() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)

            _password_resets.append(
                {
                    "id": secrets.token_hex(16),
                    "user_id": user["id"],
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                    "used_at": None,
                    "created_at": _now(),
                }
            )

            # In a real implementation, send an email here:
            # await email_service.send_reset_email(
            #     to=user["email"],
            #     reset_url=f"{FRONTEND_URL}/reset-password?token={raw_token}",
            # )

        return ForgotPasswordResponse(message=_GENERIC_MESSAGE)

    # ------------------------------------------------------------------
    # resetPassword
    # ------------------------------------------------------------------
    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _sha256(body.token)
        now = _now()

        record = next(
            (
                r
                for r in _password_resets
                if r["token_hash"] == token_hash
                and r["used_at"] is None
                and r["expires_at"] > now
            ),
            None,
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_RESET_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                },
            )

        pw_error = _validate_password_strength(body.password)
        if pw_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "WEAK_PASSWORD",
                    "message": pw_error,
                    "details": {"field": "password"},
                },
            )

        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PASSWORD_MISMATCH",
                    "message": "Passwords do not match.",
                    "details": {"field": "confirm_password"},
                },
            )

        user = next(
            (u for u in _users.values() if u["id"] == record["user_id"]),
            None,
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_RESET_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                },
            )

        user["password_hash"] = _hash_password(body.password)
        user["updated_at"] = now
        record["used_at"] = now

        # Revoke all refresh tokens for this user
        for rt in _refresh_tokens:
            if rt["user_id"] == user["id"] and rt["revoked_at"] is None:
                rt["revoked_at"] = now

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    # ------------------------------------------------------------------
    # me
    # ------------------------------------------------------------------
    async def me(
        self, credentials: Optional[HTTPAuthorizationCredentials]
    ) -> MeResponse:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "MISSING_TOKEN", "message": "Authentication required."},
            )
        payload = _decode_access_token(credentials.credentials)
        user = next(
            (u for u in _users.values() if u["id"] == payload["sub"]),
            None,
        )
        if user is None or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Invalid token."},
            )
        return MeResponse(
            id=user["id"],
            fullName=user["full_name"],
            email=user["email"],
        )

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------
    async def logout(
        self,
        body: LogoutRequest,
        credentials: Optional[HTTPAuthorizationCredentials],
        response: Response,
    ) -> LogoutResponse:
        if credentials is not None:
            try:
                payload = _decode_access_token(credentials.credentials)
                user_id = payload.get("sub")
                now = _now()
                for rt in _refresh_tokens:
                    if rt["user_id"] == user_id and rt["revoked_at"] is None:
                        rt["revoked_at"] = now
            except HTTPException:
                pass

        response.delete_cookie(key="refresh_token", path="/auth/refresh")
        return LogoutResponse(message="Logged out successfully.")

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------
    async def refresh(
        self,
        credentials: Optional[HTTPAuthorizationCredentials],
        response: Response,
    ) -> RefreshResponse:
        # In a real implementation, read refresh token from the httpOnly cookie.
        # Here we accept it from the Authorization header as a fallback for testing.
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "MISSING_TOKEN", "message": "Authentication required."},
            )

        raw_token = credentials.credentials
        token_hash = _sha256(raw_token)
        now = _now()

        record = next(
            (
                rt
                for rt in _refresh_tokens
                if rt["token_hash"] == token_hash
                and rt["revoked_at"] is None
                and rt["expires_at"] > now
            ),
            None,
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Invalid or expired refresh token."},
            )

        # Revoke old token (rotation)
        record["revoked_at"] = now

        user = next(
            (u for u in _users.values() if u["id"] == record["user_id"]),
            None,
        )
        if user is None or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Invalid token."},
            )

        access_token = _make_access_token(user["id"], user["email"])
        new_raw_refresh = _make_refresh_token()
        remember = record["remember_me"]
        expire_days = REMEMBER_ME_EXPIRE_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        rt_expires = now + timedelta(days=expire_days)

        _refresh_tokens.append(
            {
                "id": secrets.token_hex(16),
                "user_id": user["id"],
                "token_hash": _sha256(new_raw_refresh),
                "expires_at": rt_expires,
                "revoked_at": None,
                "remember_me": remember,
                "created_at": now,
            }
        )

        response.set_cookie(
            key="refresh_token",
            value=new_raw_refresh,
            httponly=True,
            samesite="lax",
            secure=True,
            max_age=int(timedelta(days=expire_days).total_seconds()),
            path="/auth/refresh",
        )

        return RefreshResponse(
            accessToken=access_token,
            tokenType="bearer",
        )
