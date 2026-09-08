from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Password policy constants (mirrors capabilities.yaml / validation-rules.md)
# ---------------------------------------------------------------------------

MIN_LENGTH: int = 8
_UPPER_RE = re.compile(r"[A-Z]")
_LOWER_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")

# Exact messages from validation-rules.md — do NOT paraphrase
MSG_FULL_NAME_REQUIRED = "Full name is required."
MSG_FULL_NAME_MAX = "Full name must not exceed 100 characters."

MSG_EMAIL_REQUIRED = "Email address is required."
MSG_EMAIL_INVALID = "Enter a valid email address."
MSG_EMAIL_MAX = "Email must not exceed 254 characters."
MSG_EMAIL_TAKEN = "An account with this email already exists."

MSG_PASSWORD_REQUIRED = "Password is required."
MSG_PASSWORD_MIN_LENGTH = "Password must be at least 8 characters."
MSG_PASSWORD_UPPERCASE = "Password must contain at least one uppercase letter."
MSG_PASSWORD_LOWERCASE = "Password must contain at least one lowercase letter."
MSG_PASSWORD_NUMBER = "Password must contain at least one number."

MSG_CONFIRM_PASSWORD_REQUIRED = "Please confirm your password."
MSG_CONFIRM_PASSWORD_MISMATCH = "Passwords do not match."

MSG_TERMS_REQUIRED = "You must accept the terms and conditions."

MSG_LOGIN_INVALID = "Invalid email or password."

MSG_TOKEN_REQUIRED = "Reset token is required."
MSG_TOKEN_INVALID = "This password reset link is invalid or has expired."

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


# ---------------------------------------------------------------------------
# Individual field validators
# ---------------------------------------------------------------------------

def validate_full_name(value: str | None) -> list[str]:
    """Return a list of error messages for the full_name field."""
    errors: list[str] = []
    if not value or not value.strip():
        errors.append(MSG_FULL_NAME_REQUIRED)
        return errors
    if len(value) > 100:
        errors.append(MSG_FULL_NAME_MAX)
    return errors


def validate_email(value: str | None) -> list[str]:
    """Return a list of error messages for the email field."""
    errors: list[str] = []
    if not value or not value.strip():
        errors.append(MSG_EMAIL_REQUIRED)
        return errors
    if len(value) > 254:
        errors.append(MSG_EMAIL_MAX)
        return errors
    # Simple but standard RFC-5322-ish check
    if not _EMAIL_RE.match(value):
        errors.append(MSG_EMAIL_INVALID)
    return errors


def validate_password(value: str | None) -> list[str]:
    """
    Return a list of error messages for the password field.

    Rules (in order per validation-rules.md):
      1. required
      2. min length >= 8
      3. at least one uppercase letter
      4. at least one lowercase letter
      5. at least one number

    Note: require_special_character is FALSE per capabilities.yaml.
    """
    errors: list[str] = []
    if not value:
        errors.append(MSG_PASSWORD_REQUIRED)
        return errors
    if len(value) < MIN_LENGTH:
        errors.append(MSG_PASSWORD_MIN_LENGTH)
    if not _UPPER_RE.search(value):
        errors.append(MSG_PASSWORD_UPPERCASE)
    if not _LOWER_RE.search(value):
        errors.append(MSG_PASSWORD_LOWERCASE)
    if not _DIGIT_RE.search(value):
        errors.append(MSG_PASSWORD_NUMBER)
    return errors


def validate_confirm_password(
    password: str | None,
    confirm_password: str | None,
) -> list[str]:
    """Return a list of error messages for the confirm_password field."""
    errors: list[str] = []
    if not confirm_password:
        errors.append(MSG_CONFIRM_PASSWORD_REQUIRED)
        return errors
    if password != confirm_password:
        errors.append(MSG_CONFIRM_PASSWORD_MISMATCH)
    return errors


def validate_terms_accepted(value: Any) -> list[str]:
    """Return a list of error messages when the Terms checkbox is unchecked."""
    errors: list[str] = []
    if not value:
        errors.append(MSG_TERMS_REQUIRED)
    return errors


def validate_reset_token(value: str | None) -> list[str]:
    """Return a list of error messages for the reset token field."""
    errors: list[str] = []
    if not value or not value.strip():
        errors.append(MSG_TOKEN_REQUIRED)
    return errors


# ---------------------------------------------------------------------------
# Composite validators (used by the service layer)
# ---------------------------------------------------------------------------

def validate_registration(
    full_name: str | None,
    email: str | None,
    password: str | None,
    confirm_password: str | None,
    terms_accepted: Any,
) -> dict[str, list[str]]:
    """
    Run all registration field validators and return a mapping of
    field -> [error messages].  Empty lists are omitted from the result.
    """
    result: dict[str, list[str]] = {}

    full_name_errors = validate_full_name(full_name)
    if full_name_errors:
        result["full_name"] = full_name_errors

    email_errors = validate_email(email)
    if email_errors:
        result["email"] = email_errors

    password_errors = validate_password(password)
    if password_errors:
        result["password"] = password_errors

    confirm_errors = validate_confirm_password(password, confirm_password)
    if confirm_errors:
        result["confirm_password"] = confirm_errors

    terms_errors = validate_terms_accepted(terms_accepted)
    if terms_errors:
        result["terms_accepted"] = terms_errors

    return result


def validate_reset_password(
    token: str | None,
    password: str | None,
    confirm_password: str | None,
) -> dict[str, list[str]]:
    """
    Run all reset-password field validators and return a mapping of
    field -> [error messages].  Empty lists are omitted from the result.
    """
    result: dict[str, list[str]] = {}

    token_errors = validate_reset_token(token)
    if token_errors:
        result["token"] = token_errors

    password_errors = validate_password(password)
    if password_errors:
        result["password"] = password_errors

    confirm_errors = validate_confirm_password(password, confirm_password)
    if confirm_errors:
        result["confirm_password"] = confirm_errors

    return result
