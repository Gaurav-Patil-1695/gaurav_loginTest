from __future__ import annotations

from pydantic import AnyUrl, EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str

    # ------------------------------------------------------------------ #
    # JWT
    # ------------------------------------------------------------------ #
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_TTL_MINUTES: int = 15

    # ------------------------------------------------------------------ #
    # Bcrypt
    # ------------------------------------------------------------------ #
    BCRYPT_ROUNDS: int = 12

    # ------------------------------------------------------------------ #
    # Password-reset token
    # ------------------------------------------------------------------ #
    RESET_TOKEN_TTL_MINUTES: int = 60

    # ------------------------------------------------------------------ #
    # Refresh token
    # ------------------------------------------------------------------ #
    REFRESH_TOKEN_TTL_DAYS: int = 7
    REFRESH_TOKEN_TTL_DAYS_REMEMBER_ME: int = 30

    # ------------------------------------------------------------------ #
    # SMTP
    # ------------------------------------------------------------------ #
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: EmailStr
    SMTP_FROM_NAME: str = "Auth Starter"
    SMTP_USE_TLS: bool = True

    # ------------------------------------------------------------------ #
    # Rate limits
    # ------------------------------------------------------------------ #
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60
    RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS: int = 3
    RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS: int = 3600

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _database_url_not_empty(cls, v: object) -> object:
        if not v or not str(v).strip():
            raise ValueError("DATABASE_URL must not be empty")
        return v

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def _jwt_secret_not_empty(cls, v: object) -> object:
        if not v or not str(v).strip():
            raise ValueError("JWT_SECRET_KEY must not be empty")
        return v

    @field_validator("BCRYPT_ROUNDS", mode="before")
    @classmethod
    def _bcrypt_rounds_minimum(cls, v: object) -> object:
        value = int(v)  # type: ignore[arg-type]
        if value < 12:
            raise ValueError("BCRYPT_ROUNDS must be >= 12")
        return value

    @field_validator("SMTP_HOST", mode="before")
    @classmethod
    def _smtp_host_not_empty(cls, v: object) -> object:
        if not v or not str(v).strip():
            raise ValueError("SMTP_HOST must not be empty")
        return v

    @field_validator("SMTP_USERNAME", mode="before")
    @classmethod
    def _smtp_username_not_empty(cls, v: object) -> object:
        if not v or not str(v).strip():
            raise ValueError("SMTP_USERNAME must not be empty")
        return v

    @field_validator("SMTP_PASSWORD", mode="before")
    @classmethod
    def _smtp_password_not_empty(cls, v: object) -> object:
        if not v or not str(v).strip():
            raise ValueError("SMTP_PASSWORD must not be empty")
        return v


def _load_settings() -> Settings:
    """Instantiate Settings eagerly so missing variables raise at import time."""
    return Settings()  # type: ignore[call-arg]


settings: Settings = _load_settings()
