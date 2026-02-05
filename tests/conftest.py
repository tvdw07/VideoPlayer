from __future__ import annotations
import re
from pathlib import Path

import pytest

from videoplayer import create_app, User, db
from videoplayer.security import hash_password


def _extract_csrf(html: str) -> str:
    """
    Extract CSRF token from HTML form:
      <input type="hidden" name="csrf_token" value="...">
    """
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert m, "CSRF token not found in HTML"
    return m.group(1)


@pytest.fixture()
def app(tmp_path: Path):
    """
    Create a fresh app + SQLite DB per test.
    We use a temp file DB (not in-memory) to avoid connection edge cases.
    """
    db_path = tmp_path / "test.db"

    app = create_app(
        {
            "TESTING": True,
            "DEBUG": False,
            "AUTH_ENABLED": True,
            "WTF_CSRF_TIME_LIMIT": None,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path.as_posix()}",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            # Keep cookies predictable in tests
            "SESSION_COOKIE_SECURE": False,
            "REMEMBER_COOKIE_SECURE": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user(app) -> User:
    """Create a normal test user."""
    with app.app_context():
        u = User(username="testuser", password_hash=hash_password("testpass"), is_admin=False)
        db.session.add(u)
        db.session.commit()
        return u


def login(client, next_url: str | None = None) -> None:
    """Helper: perform a CSRF-protected login."""
    url = "/login"
    if next_url:
        url = f"/login?next={next_url}"

    r = client.get(url)
    assert r.status_code == 200
    csrf_token = _extract_csrf(r.get_data(as_text=True))

    data = {
        "csrf_token": csrf_token,
        "username": "testuser",
        "password": "testpass",
        "next": next_url or "",
    }
    r2 = client.post("/login", data=data, follow_redirects=False)
    assert r2.status_code in (302, 303)


@pytest.fixture()
def auth_client(client, user):
    """Client already logged in."""
    login(client)
    return client
