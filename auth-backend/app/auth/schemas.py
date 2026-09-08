from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: EmailStr
    password: str
    confirm_password: str


class RegisterResponse(BaseModel):
    message: str
    user_id: str


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


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
    confirm_password: str


class ResetPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------

class MeResponse(BaseModel):
    id: str
    full_name: str
    email: str
    is_active: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail] = []


class ErrorResponse(BaseModel):
    error: ErrorBody
