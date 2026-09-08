from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request, Response, status

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
from app.core.config import settings
from app.models.user import User
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_token,
)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_reset_repository: PasswordResetRepository,
    ) -> None:
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository
        self.password_reset_repository = password_reset_repository

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = await self.user_repository.get_by_email(body.email)
        if user is None or not verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": {},
                },
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "ACCOUNT_INACTIVE",
                    "message": "Invalid email or password.",
                    "details": {},
                },
            )

        access_token = create_access_token({"sub": str(user.id)})
        raw_refresh_token = create_refresh_token()
        token_hash = hash_token(raw_refresh_token)
        remember_me = body.remember_me if body.remember_me is not None else False
        expires_at = datetime.now(timezone.utc) + (
            timedelta(days=settings.REFRESH_TOKEN_REMEMBER_DAYS)
            if remember_me
            else timedelta(days=settings.REFRESH_TOKEN_DAYS)
        )
        await self.refresh_token_repository.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            remember_me=remember_me,
        )

        response.set_cookie(
            key="refresh_token",
            value=raw_refresh_token,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            max_age=int(expires_at.timestamp() - datetime.now(timezone.utc).timestamp()),
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
        )

    async def register(self, body: RegisterRequest) -> RegisterResponse:
        existing = await self.user_repository.get_by_email(body.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_TAKEN",
                    "message": "An account with this email already exists.",
                    "details": {"field": "email"},
                },
            )
        password_hash = hash_password(body.password)
        user = await self.user_repository.create(
            full_name=body.full_name,
            email=body.email,
            password_hash=password_hash,
        )
        return RegisterResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def forgotPassword(
        self, body: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        user = await self.user_repository.get_by_email(body.email)
        if user is not None and user.is_active:
            import secrets

            raw_token = secrets.token_urlsafe(32)
            token_hash = hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
            )
            await self.password_reset_repository.create(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            # Email sending is handled by the email service (out of scope here).
            # In production, dispatch the reset link containing raw_token.

        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    async def resetPassword(
        self, body: ResetPasswordRequest
    ) -> ResetPasswordResponse:
        token_hash = hash_token(body.token)
        reset_record = await self.password_reset_repository.get_valid_by_hash(
            token_hash=token_hash,
            now=datetime.now(timezone.utc),
        )
        if reset_record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_RESET_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": {},
                },
            )
        new_hash = hash_password(body.password)
        await self.user_repository.update_password(
            user_id=reset_record.user_id,
            password_hash=new_hash,
        )
        await self.password_reset_repository.mark_used(
            record_id=reset_record.id,
            used_at=datetime.now(timezone.utc),
        )
        await self.refresh_token_repository.revoke_all_for_user(
            user_id=reset_record.user_id,
            revoked_at=datetime.now(timezone.utc),
        )
        return ResetPasswordResponse(
            message="Your password has been reset successfully."
        )

    async def me(self, current_user: User) -> MeResponse:
        return MeResponse(
            id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
        )

    async def logout(
        self,
        body: LogoutRequest,
        response: Response,
        request: Request,
        current_user: User,
    ) -> LogoutResponse:
        raw_refresh_token: Optional[str] = (
            body.refresh_token
            if body.refresh_token
            else request.cookies.get("refresh_token")
        )
        if raw_refresh_token:
            token_hash = hash_token(raw_refresh_token)
            await self.refresh_token_repository.revoke_by_hash(
                token_hash=token_hash,
                revoked_at=datetime.now(timezone.utc),
            )
        response.delete_cookie(key="refresh_token")
        return LogoutResponse(message="Logged out successfully.")

    async def refresh(
        self,
        body: RefreshRequest,
        response: Response,
        request: Request,
    ) -> RefreshResponse:
        raw_refresh_token: Optional[str] = (
            body.refresh_token
            if body.refresh_token
            else request.cookies.get("refresh_token")
        )
        if not raw_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "MISSING_REFRESH_TOKEN",
                    "message": "Refresh token is missing.",
                    "details": {},
                },
            )
        token_hash = hash_token(raw_refresh_token)
        record = await self.refresh_token_repository.get_valid_by_hash(
            token_hash=token_hash,
            now=datetime.now(timezone.utc),
        )
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": {},
                },
            )
        # Rotate: revoke old token
        await self.refresh_token_repository.revoke_by_hash(
            token_hash=token_hash,
            revoked_at=datetime.now(timezone.utc),
        )

        import secrets

        new_raw_token = secrets.token_urlsafe(32)
        new_token_hash = hash_token(new_raw_token)
        remember_me = record.remember_me
        expires_at = datetime.now(timezone.utc) + (
            timedelta(days=settings.REFRESH_TOKEN_REMEMBER_DAYS)
            if remember_me
            else timedelta(days=settings.REFRESH_TOKEN_DAYS)
        )
        await self.refresh_token_repository.create(
            user_id=record.user_id,
            token_hash=new_token_hash,
            expires_at=expires_at,
            remember_me=remember_me,
        )

        access_token = create_access_token({"sub": str(record.user_id)})

        response.set_cookie(
            key="refresh_token",
            value=new_raw_token,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            max_age=int(expires_at.timestamp() - datetime.now(timezone.utc).timestamp()),
        )

        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
        )
