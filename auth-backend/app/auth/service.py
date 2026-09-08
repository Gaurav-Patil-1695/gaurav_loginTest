from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, status

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

# ---------------------------------------------------------------------------
# Environment-driven configuration
# ---------------------------------------------------------------------------

SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
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
PASSWORD_RESET_EXPIRE_MINUTES: int = int(
    os.environ.get("PASSWORD_RESET_EXPIRE_MINUTES", "60")
)
REFRESH_COOKIE_NAME: str = "refresh_token"

# ---------------------------------------------------------------------------
# In-memory stores (replace with real DB repositories in production)
# ---------------------------------------------------------------------------
# users: {email: {id, full_name, email, password_hash, is_active,
#         created_at, updated_at}}
_users: dict[str, dict] = {}
# refresh_tokens: {token_hash: {id, user_id, token_hash, expires_at,
#                  revoked_at, remember_me, created_at}}
_refresh_tokens: dict[str, dict] = {}
# password_resets: {token_hash: {id, user_id, token_hash, expires_at,
#                   used_at, created_at}}
_password_resets: dict[str, dict] = {}
# revoked access tokens: {jti}
_revoked_jtis: set[str] = set()

# ---------------------------------------------------------------------------
# Shared error message constants
# ---------------------------------------------------------------------------

_MSG_INVALID_OR_EXPIRED_REFRESH = "Invalid or expired refresh token."
_MSG_INVALID_OR_EXPIRED_RESET = "Password reset token is invalid or has expired."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_token() -> str:
    return secrets.token_urlsafe(64)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: str, email: str) -> tuple[str, str]:
    """Return (encoded_jwt, jti)."""
    jti = secrets.token_hex(16)
    expire = _now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "jti": jti,
        "exp": expire,
        "iat": _now(),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Token has expired.",
                    "details": {},
                }
            },
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Invalid token.",
                    "details": {},
                }
            },
        )
    return payload


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_ME_DAYS * 86400
        if remember_me
        else REFRESH_TOKEN_EXPIRE_DAYS * 86400
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
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/auth/refresh",
        httponly=True,
        samesite="lax",
        secure=True,
    )


def _validate_password_policy(password: str) -> str | None:
    """Return an error message if the password fails policy, else None."""
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

    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Passwords do not match.",
                        "details": {"confirm_password": "Passwords do not match."},
                    }
                },
            )

        policy_error = _validate_password_policy(body.password)
        if policy_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": policy_error,
                        "details": {"password": policy_error},
                    }
                },
            )

        if body.email.lower() in _users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": {
                            "email": "An account with this email already exists.",
                        },
                    }
                },
            )

        user_id = secrets.token_hex(16)
        now = _now()
        user: dict = {
            "id": user_id,
            "full_name": body.full_name,
            "email": body.email.lower(),
            "password_hash": _hash_password(body.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        _users[body.email.lower()] = user

        return RegisterResponse(
            id=user_id,
            fullName=body.full_name,
            email=body.email.lower(),
        )

    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------
    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = _users.get(body.email.lower())

        if user is None or not _verify_password(body.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "details": {},
                    }
                },
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": "Account is inactive.",
                        "details": {},
                    }
                },
            )

        access_token, _jti = _create_access_token(user["id"], user["email"])

        remember_me: bool = body.remember_me if body.remember_me is not None else False
        raw_refresh = _generate_token()
        refresh_hash = _sha256(raw_refresh)
        expire_days = (
            REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me
            else REFRESH_TOKEN_EXPIRE_DAYS
        )
        expires_at = _now() + timedelta(days=expire_days)
        _refresh_tokens[refresh_hash] = {
            "id": secrets.token_hex(16),
            "user_id": user["id"],
            "token_hash": refresh_hash,
            "expires_at": expires_at,
            "revoked_at": None,
            "remember_me": remember_me,
            "created_at": _now(),
        }

        _set_refresh_cookie(response, raw_refresh, remember_me)

        return LoginResponse(
            accessToken=access_token,
            tokenType="bearer",
        )

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------
    async def refresh(self, request: Request, response: Response) -> RefreshResponse:
        raw_refresh: str | None = request.cookies.get(REFRESH_COOKIE_NAME)

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
        record = _refresh_tokens.get(token_hash)

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": _MSG_INVALID_OR_EXPIRED_REFRESH,
                        "details": {},
                    }
                },
            )

        if record["revoked_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "REFRESH_TOKEN_REVOKED",
                        "message": _MSG_INVALID_OR_EXPIRED_REFRESH,
                        "details": {},
                    }
                },
            )

        if _now() > record["expires_at"]:
            record["revoked_at"] = _now()
            _clear_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "REFRESH_TOKEN_EXPIRED",
                        "message": _MSG_INVALID_OR_EXPIRED_REFRESH,
                        "details": {},
                    }
                },
            )

        # Revoke the old refresh token (rotation)
        record["revoked_at"] = _now()

        # Locate the user
        user = next(
            (u for u in _users.values() if u["id"] == record["user_id"]), None
        )
        if user is None or not user["is_active"]:
            _clear_refresh_cookie(response)
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

        # Issue new access token
        new_access_token, _jti = _create_access_token(user["id"], user["email"])

        # Issue new refresh token
        remember_me: bool = record["remember_me"]
        new_raw_refresh = _generate_token()
        new_refresh_hash = _sha256(new_raw_refresh)
        expire_days = (
            REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me
            else REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_expires_at = _now() + timedelta(days=expire_days)
        _refresh_tokens[new_refresh_hash] = {
            "id": secrets.token_hex(16),
            "user_id": user["id"],
            "token_hash": new_refresh_hash,
            "expires_at": new_expires_at,
            "revoked_at": None,
            "remember_me": remember_me,
            "created_at": _now(),
        }

        _set_refresh_cookie(response, new_raw_refresh, remember_me)

        return RefreshResponse(
            accessToken=new_access_token,
            tokenType="bearer",
        )

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------
    async def logout(
        self,
        request: Request,
        response: Response,
        access_token: str | None,
    ) -> None:
        # Revoke access token JTI if provided and valid
        if access_token:
            try:
                payload = _decode_access_token(access_token)
                jti = payload.get("jti")
                if jti:
                    _revoked_jtis.add(jti)
            except HTTPException:
                pass

        # Revoke refresh token if cookie is present
        raw_refresh: str | None = request.cookies.get(REFRESH_COOKIE_NAME)
        if raw_refresh:
            token_hash = _sha256(raw_refresh)
            record = _refresh_tokens.get(token_hash)
            if record and record["revoked_at"] is None:
                record["revoked_at"] = _now()

        _clear_refresh_cookie(response)

    # ------------------------------------------------------------------
    # me
    # ------------------------------------------------------------------
    async def me(self, access_token: str) -> MeResponse:
        payload = _decode_access_token(access_token)

        jti = payload.get("jti")
        if jti and jti in _revoked_jtis:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "TOKEN_REVOKED",
                        "message": "Token has been revoked.",
                        "details": {},
                    }
                },
            )

        email: str = payload.get("email", "")
        user = _users.get(email.lower())
        if user is None or not user["is_active"]:
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

        return MeResponse(
            id=user["id"],
            fullName=user["full_name"],
            email=user["email"],
            isActive=user["is_active"],
            createdAt=user["created_at"],
        )

    # ------------------------------------------------------------------
    # forgotPassword
    # ------------------------------------------------------------------
    async def forgotPassword(
        self, body: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        user = _users.get(body.email.lower())

        if user is not None and user["is_active"]:
            raw_token = _generate_token()
            token_hash = _sha256(raw_token)
            expires_at = _now() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
            _password_resets[token_hash] = {
                "id": secrets.token_hex(16),
                "user_id": user["id"],
                "token_hash": token_hash,
                "expires_at": expires_at,
                "used_at": None,
                "created_at": _now(),
            }
            # In production, email the raw_token to user["email"] here.

        # Always return the same generic response (enumeration resistance)
        return ForgotPasswordResponse(
            message=(
                "If an account with that email exists, a password reset link"
                " has been sent."
            )
        )

    # ------------------------------------------------------------------
    # resetPassword
    # ------------------------------------------------------------------
    async def resetPassword(
        self, body: ResetPasswordRequest
    ) -> ResetPasswordResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Passwords do not match.",
                        "details": {"confirm_password": "Passwords do not match."},
                    }
                },
            )

        policy_error = _validate_password_policy(body.password)
        if policy_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": policy_error,
                        "details": {"password": policy_error},
                    }
                },
            )

        token_hash = _sha256(body.token)
        record = _password_resets.get(token_hash)

        invalid_exc = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_RESET_TOKEN",
                    "message": _MSG_INVALID_OR_EXPIRED_RESET,
                    "details": {},
                }
            },
        )

        if record is None:
            raise invalid_exc
        if record["used_at"] is not None:
            raise invalid_exc
        if _now() > record["expires_at"]:
            raise invalid_exc

        user = next(
            (u for u in _users.values() if u["id"] == record["user_id"]), None
        )
        if user is None:
            raise invalid_exc

        user["password_hash"] = _hash_password(body.password)
        user["updated_at"] = _now()
        record["used_at"] = _now()

        # Revoke all existing refresh tokens for this user
        for rt in _refresh_tokens.values():
            if rt["user_id"] == user["id"] and rt["revoked_at"] is None:
                rt["revoked_at"] = _now()

        return ResetPasswordResponse(message="Password has been reset successfully.")
