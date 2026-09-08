from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config.settings import settings


def _build_reset_link(raw_token: str) -> str:
    """Construct the password-reset URL using APP_BASE_URL."""
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/reset-password?token={raw_token}"


def _build_plain_text_body(reset_link: str) -> str:
    return (
        "You requested a password reset.\n\n"
        "Click the link below to reset your password:\n"
        f"{reset_link}\n\n"
        "This link will expire in "
        f"{settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.\n\n"
        "If you did not request a password reset, please ignore this email."
    )


def _build_html_body(reset_link: str) -> str:
    return (
        "<!DOCTYPE html>"
        "<html><body>"
        "<p>You requested a password reset.</p>"
        "<p>Click the link below to reset your password:</p>"
        f'<p><a href=\"{reset_link}\">{reset_link}</a></p>'
        f"<p>This link will expire in "
        f"{settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>"
        "<p>If you did not request a password reset, please ignore this email.</p>"
        "</body></html>"
    )


def send_reset_email(to_email: str, raw_token: str) -> None:
    """
    Send a password-reset email to *to_email*.

    Builds the reset link as APP_BASE_URL/reset-password?token=<raw_token>
    and delivers the message via SMTP using the SMTP_* settings.
    """
    reset_link = _build_reset_link(raw_token)

    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset your password"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email

    plain_part = MIMEText(_build_plain_text_body(reset_link), "plain", "utf-8")
    html_part = MIMEText(_build_html_body(reset_link), "html", "utf-8")

    # RFC 2046: last part is preferred; attach HTML last
    message.attach(plain_part)
    message.attach(html_part)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        if settings.SMTP_TLS:
            server.starttls()
            server.ehlo()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(
            settings.SMTP_FROM_EMAIL,
            [to_email],
            message.as_string(),
        )
