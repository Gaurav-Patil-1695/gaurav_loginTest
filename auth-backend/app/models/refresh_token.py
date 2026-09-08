from datetime import datetime
from typing import Optional


class RefreshToken:
    """Row mapping for the refresh_tokens table."""

    def __init__(
        self,
        id: int,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        revoked_at: Optional[datetime],
        remember_me: bool,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.revoked_at = revoked_at
        self.remember_me = remember_me
        self.created_at = created_at

    @classmethod
    def from_row(cls, row: dict) -> "RefreshToken":
        """Construct a RefreshToken from a database row dict."""
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
            remember_me=row["remember_me"],
            created_at=row["created_at"],
        )

    def to_dict(self) -> dict:
        """Serialize the RefreshToken to a plain dict (excludes token_hash)."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
            "remember_me": self.remember_me,
            "created_at": self.created_at,
        }

    @property
    def is_revoked(self) -> bool:
        """Return True if the token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        """Return True if the token has passed its expiry time."""
        return datetime.utcnow() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Return True if the token is neither revoked nor expired."""
        return not self.is_revoked and not self.is_expired

    def __repr__(self) -> str:
        return (
            f"RefreshToken(id={self.id!r}, user_id={self.user_id!r}, "
            f"remember_me={self.remember_me!r}, is_valid={self.is_valid!r})"
        )
