from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Response

from app.auth.schemas import LoginRequest, LoginResponse, TokenPair, UserPublic
from app.db import get_db_connection


ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_ME_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_REMEMBER_ME_DAYS", "30")
)
JWT_SECRET: str = os.environ.get("JWT_SECRET", "changeme")
JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"

INVALID_CREDENTIALS_MESSAGE: str = "Invalid email or password."
ACCOUNT_INACTIVE_MESSAGE: str = "Invalid email or password."


class AuthService:
    """Service layer for authentication operations."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def login(
        self,
        payload: LoginRequest,
        response: Response,
    ) -> LoginResponse:
        """Authenticate a user with email and password.

        Returns a LoginResponse containing the access token and public user
        info.  Sets the refresh token in an httpOnly, SameSite=Lax cookie.

        Raises HTTPException(401) for any authentication failure so that the
        handler communicates the same message regardless of the failure
        reason (enumeration resistance, NFR-03).
        """
        from fastapi import HTTPException, status

        user = await self._get_user_by_email(payload.email)

        # Enumeration resistance: same error for "not found" and "wrong password"
        if user is None or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": INVALID_CREDENTIALS_MESSAGE,
                        "details": [],
                    }
                },
            )

        password_matches = bcrypt.checkpw(
            payload.password.encode("utf-8"),
            user["password_hash"].encode("utf-8"),
        )
        if not password_matches:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": INVALID_CREDENTIALS_MESSAGE,
                        "details": [],
                    }
                },
            )

        access_token = self._create_access_token(user_id=user["id"], email=user["email"])
        refresh_token_plain, refresh_token_hash = self._generate_refresh_token()

        remember = payload.remember_me if payload.remember_me is not None else False
        refresh_expires_days = (
            REFRESH_TOKEN_REMEMBER_ME_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=refresh_expires_days)

        await self._store_refresh_token(
            user_id=user["id"],
            token_hash=refresh_token_hash,
            expires_at=refresh_expires_at,
            remember_me=remember,
        )

        # Set refresh token in httpOnly, SameSite=Lax cookie
        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=refresh_token_plain,
            httponly=True,
            samesite="lax",
            secure=True,
            expires=int(refresh_expires_days * 24 * 3600),
            path="/auth/refresh",
        )

        user_public = UserPublic(
            id=user["id"],
            full_name=user["full_name"],
            email=user["email"],
            is_active=user["is_active"],
            created_at=user["created_at"],
        )

        return LoginResponse(
            tokens=TokenPair(
                access_token=access_token,
                token_type="bearer",
            ),
            user=user_public,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_access_token(self, *, user_id: str, email: str) -> str:
        """Create a signed JWT access token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        claims = {
            "sub": str(user_id),
            "email": email,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
        return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def _generate_refresh_token(self) -> tuple[str, str]:
        """Return (plaintext_token, sha256_hash_hex) for a new refresh token."""
        import hashlib
        import secrets

        plain = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(plain.encode("utf-8")).hexdigest()
        return plain, token_hash

    async def _get_user_by_email(self, email: str) -> Optional[dict]:
        """Fetch a user row by email from the database.

        Returns a dict with keys matching the `users` table columns, or
        None if no such user exists.
        """
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, full_name, email, password_hash, is_active, created_at, updated_at
                FROM users
                WHERE email = $1
                LIMIT 1
                """,
                email.lower(),
            )
        if row is None:
            return None
        return dict(row)

    async def _store_refresh_token(
        self,
        *,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        remember_me: bool,
    ) -> None:
        """Persist a hashed refresh token to the `refresh_tokens` table."""
        async with get_db_connection() as conn:
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at, remember_me)
                VALUES ($1, $2, $3, $4)
                """,
                user_id,
                token_hash,
                expires_at,
                remember_me,
            )
