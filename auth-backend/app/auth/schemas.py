from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr = Field(..., description="The user's email address.")
    password: str = Field(..., description="The user's password.")
    remember_me: Optional[bool] = Field(
        default=False,
        description="When True the refresh token lifetime is extended.",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TokenPair(BaseModel):
    """Access token and its type."""

    access_token: str = Field(..., description="Signed JWT access token.")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'.")


class UserPublic(BaseModel):
    """Public-safe representation of a user."""

    id: str = Field(..., description="Unique user identifier.")
    full_name: str = Field(..., description="User's full name.")
    email: str = Field(..., description="User's email address.")
    is_active: bool = Field(..., description="Whether the account is active.")
    created_at: datetime = Field(..., description="Account creation timestamp.")


class LoginResponse(BaseModel):
    """Response body for POST /auth/login."""

    tokens: TokenPair = Field(..., description="Access token payload.")
    user: UserPublic = Field(..., description="Authenticated user details.")


# ---------------------------------------------------------------------------
# Error schemas
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """A single field-level validation detail."""

    field: Optional[str] = Field(default=None, description="The field that failed validation.")
    message: str = Field(..., description="Human-readable error message.")


class ErrorEnvelope(BaseModel):
    """Inner envelope for error responses."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable top-level error message.")
    details: List[ErrorDetail] = Field(
        default_factory=list,
        description="Per-field validation details.",
    )


class ErrorResponse(BaseModel):
    """Outer envelope for all error responses."""

    error: ErrorEnvelope = Field(..., description="Error payload.")
