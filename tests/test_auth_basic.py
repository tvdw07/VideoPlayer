from __future__ import annotations

from urllib.parse import urlparse


def test_login_page_ok(client):
    r = client.get("/login")
    assert r.status_code == 200


def test_protected_browse_requires_login(client):
    # Adjust if your browse route differs.
    r = client.get("/browse/", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in r.headers.get("Location", "")


def test_login_success_redirects_to_browse(auth_client):
    r = auth_client.get("/browse/", follow_redirects=False)
    assert r.status_code == 200


def test_open_redirect_is_blocked(client, user):
    """
    Attempt login with next=https://example.com.
    After login, app must NOT redirect off-site.
    """
    next_url = "https://example.com"
    r = client.get(f"/login?next={next_url}")
    assert r.status_code == 200

    # login helper is in conftest.py, but we can reproduce inline:
    html = r.get_data(as_text=True)
    import re
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert m
    csrf_token = m.group(1)

    data = {
        "csrf_token": csrf_token,
        "username": "testuser",
        "password": "testpass",
        "next": next_url,
    }

    r2 = client.post("/login", data=data, follow_redirects=False)
    assert r2.status_code in (302, 303)

    loc = r2.headers.get("Location", "")
    # Must not be absolute external URL
    parsed = urlparse(loc)
    assert parsed.scheme == "" and parsed.netloc == ""
