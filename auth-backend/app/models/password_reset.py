from datetime import datetime


class PasswordReset:
    """In-memory representation of the password_resets table row."""

    def __init__(
        self,
        id: str,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        used_at: datetime | None,
        created_at: datetime,
    ) -> None:
        self.id: str = id
        self.user_id: str = user_id
        self.token_hash: str = token_hash
        self.expires_at: datetime = expires_at
        self.used_at: datetime | None = used_at
        self.created_at: datetime = created_at

    def is_valid(self, now: datetime) -> bool:
        """Return True when the token has not been used and has not expired."""
        return self.used_at is None and self.expires_at > now

    def mark_used(self, now: datetime) -> None:
        """Consume the token so it cannot be reused."""
        self.used_at = now

    def to_dict(self) -> dict:
        """Serialise to a plain dict mirroring the password_resets schema."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token_hash": self.token_hash,
            "expires_at": self.expires_at,
            "used_at": self.used_at,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PasswordReset":
        """Reconstruct a PasswordReset instance from a plain dict."""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            token_hash=data["token_hash"],
            expires_at=data["expires_at"],
            used_at=data.get("used_at"),
            created_at=data["created_at"],
        )
