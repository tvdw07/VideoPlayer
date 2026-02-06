from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

MAX_FAILED_LOGINS = int(os.getenv("MAX_FAILED_LOGINS", "5"))
LOCK_MINUTES = int(os.getenv("LOCK_MINUTES", "15"))


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

    def register_failed_login(self) -> None:
        """Increase failed login counter and lock account if threshold reached."""
        if self.locked_until is not None and self.locked_until > utcnow():
            return

        self.failed_login_count += 1
        if self.failed_login_count >= MAX_FAILED_LOGINS:
            self.locked_until = utcnow() + timedelta(minutes=LOCK_MINUTES)

    def register_successful_login(self) -> None:
        """Reset brute-force protection fields on successful login."""
        self.failed_login_count = 0
        self.locked_until = None
        self.last_login_at = utcnow()


class AppSetting(db.Model):
    __tablename__ = "app_settings"

    # only allow known keys (enforced in app logic)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)

    # typed storage (so you don't have to parse strings)
    int_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bool_value: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        return f"<AppSetting key={self.key!r} int={self.int_value!r} bool={self.bool_value!r}>"
