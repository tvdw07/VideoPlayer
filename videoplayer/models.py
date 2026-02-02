from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    """
    Minimal User model for session-based auth.

    Security notes:
    - store ONLY password hashes (argon2), never plaintext
    - keep username unique + indexed
    - include fields for brute-force mitigation (lockout) in the DB
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(db.String(64), index=True, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)

    # Account lifecycle
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)

    # Brute-force mitigation (optional to use immediately, but good to have now)
    failed_login_count: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)

    # Optional: "remember me" invalidation (logout everywhere) later
    session_version: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("failed_login_count >= 0", name="ck_users_failed_login_count_nonneg"),
        CheckConstraint("session_version >= 1", name="ck_users_session_version_min1"),
    )

    def can_login(self) -> bool:
        """Central place to check if account is enabled/unlocked."""
        if not self.is_active:
            return False
        if self.locked_until is not None and self.locked_until > utcnow():
            return False
        return True
