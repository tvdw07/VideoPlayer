from __future__ import annotations

import re


def _extract_csrf(html: str) -> str:
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert m, "CSRF token not found"
    return m.group(1)


def test_logout_requires_csrf(auth_client):
    # Without CSRF token -> should be rejected (Flask-WTF usually returns 400)
    r = auth_client.post("/logout", data={}, follow_redirects=False)
    assert r.status_code == 400


def test_logout_with_csrf_works(auth_client):
    # Need CSRF token from any rendered page that includes csrf_token()
    # Base template has logout form (POST) -> easiest: fetch /browse/ and parse token.
    page = auth_client.get("/browse/")
    assert page.status_code == 200

    csrf_token = _extract_csrf(page.get_data(as_text=True))

    r = auth_client.post("/logout", data={"csrf_token": csrf_token}, follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in r.headers.get("Location", "")
