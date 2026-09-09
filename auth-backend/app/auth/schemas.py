from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    full_name: str = Field(..., alias="fullName")
    email: EmailStr
    password: str
    confirm_password: str = Field(..., alias="confirmPassword")

    model_config = {"populate_by_name": True}


class RegisterResponse(BaseModel):
    id: str
    full_name: str = Field(..., alias="fullName")
    email: str
    role: str

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool | None = Field(None, alias="rememberMe")

    model_config = {"populate_by_name": True}


class LoginResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(..., alias="tokenType")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


class RefreshResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(..., alias="tokenType")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Logout  (no body schemas needed — 204 No Content)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------


class MeResponse(BaseModel):
    id: str
    full_name: str = Field(..., alias="fullName")
    email: str
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    role: str

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Reset Password
# ---------------------------------------------------------------------------


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str = Field(..., alias="confirmPassword")

    model_config = {"populate_by_name": True}


class ResetPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Shared error envelope (used internally; FastAPI serialises via HTTPException)
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict


class ErrorResponse(BaseModel):
    error: ErrorDetail
