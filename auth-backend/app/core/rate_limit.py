from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings

# ---------------------------------------------------------------------------
# Shared limiter instance (NFR-08)
# ---------------------------------------------------------------------------
# The limiter uses the client's remote address as the key function so that
# rate limits are applied per IP address.

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Limit strings — driven by environment settings
# ---------------------------------------------------------------------------
# These are resolved at import time from settings so that the values remain
# configurable via environment variables without code changes.

LOGIN_LIMIT: str = settings.LOGIN_RATE_LIMIT
FORGOT_PASSWORD_LIMIT: str = settings.FORGOT_PASSWORD_RATE_LIMIT
