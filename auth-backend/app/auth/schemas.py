from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = None


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: EmailStr
    password: str
    confirm_password: str


class RegisterResponse(BaseModel):
    id: str
    fullName: str
    email: EmailStr


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
    fullName: str
    email: EmailStr


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class LogoutRequest(BaseModel):
    pass


class LogoutResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


class RefreshResponse(BaseModel):
    accessToken: str
    tokenType: str


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
