from datetime import datetime


class User:
    """Row mapping for the users table."""

    def __init__(
        self,
        id: int,
        full_name: str,
        email: str,
        password_hash: str,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_row(cls, row: dict) -> "User":
        """Construct a User from a database row dict."""
        return cls(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            password_hash=row["password_hash"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        """Serialize the User to a plain dict (excludes password_hash)."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, email={self.email!r}, "
            f"is_active={self.is_active!r})"
        )
