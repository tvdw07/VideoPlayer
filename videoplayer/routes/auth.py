from __future__ import annotations

from urllib.parse import urlparse, urljoin

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func

from ..extensions import db, limiter
from ..models import User
from ..security import verify_password


auth_bp = Blueprint("auth", __name__)


def is_safe_redirect(target: str) -> bool:
    """Prevent open-redirects: allow only same-host redirects."""
    if not target:
        return False
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ("http", "https") and host_url.netloc == redirect_url.netloc


@auth_bp.get("/login")
@limiter.limit("10 per minute")
def login():
    if not current_app.config.get("AUTH_ENABLED", True):
        return redirect(url_for("browse.index"))

    if current_user.is_authenticated:
        return redirect(url_for("browse.index"))

    return render_template("login.html")


@auth_bp.post("/login")
@limiter.limit("5 per minute")
def login_post():
    if not current_app.config.get("AUTH_ENABLED", True):
        return redirect(url_for("browse.index"))

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    remember = bool(request.form.get("remember"))
    next_url = request.form.get("next") or request.args.get("next") or ""

    # Case-insensitive lookup
    user = (
        db.session.query(User)
        .filter(func.lower(User.username) == username.lower())
        .one_or_none()
    )

    # Generic message to avoid account enumeration
    if user is None or (not user.can_login()) or (not verify_password(user.password_hash, password)):
        flash("Login fehlgeschlagen.", "danger")
        return redirect(url_for("auth.login", next=next_url))

    # Successful login: reset counters (optional, but good)
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = db.func.now()
    db.session.commit()

    login_user(user, remember=remember)

    if is_safe_redirect(next_url):
        return redirect(next_url)

    return redirect(url_for("browse.browse"))


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
