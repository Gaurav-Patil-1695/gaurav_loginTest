from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False


class LoginUserInfo(BaseModel):
    id: str
    fullName: str
    email: EmailStr


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str
    user: LoginUserInfo


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    fullName: str = Field(..., min_length=1)
    email: EmailStr
    password: str
    confirmPassword: str


class RegisterUserInfo(BaseModel):
    id: str
    fullName: str
    email: EmailStr


class RegisterResponse(BaseModel):
    message: str
    user: RegisterUserInfo


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
    confirmPassword: str


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


class LogoutResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


class RefreshResponse(BaseModel):
    accessToken: str
    tokenType: str


# ---------------------------------------------------------------------------
# Error envelope (shared)
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail
