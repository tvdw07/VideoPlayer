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
        return redirect(url_for("browse.browse"))

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    remember = bool(request.form.get("remember"))
    next_url = request.form.get("next") or request.args.get("next") or ""

    generic_err = "Login fehlgeschlagen."

    if not username or not password:
        flash(generic_err, "danger")
        return redirect(url_for("auth.login", next=next_url))

    # Case-insensitive lookup
    user = (
        db.session.query(User)
        .filter(func.lower(User.username) == username.lower())
        .one_or_none()
    )

    # If user doesn't exist: generic error
    if user is None:
        flash(generic_err, "danger")
        return redirect(url_for("auth.login", next=next_url))

    # If user exists but is locked/disabled:
    if not user.can_login():
        flash(generic_err, "danger")
        return redirect(url_for("auth.login", next=next_url))

    # Verify password
    if not verify_password(user.password_hash, password):
        user.register_failed_login()
        db.session.commit()
        flash(generic_err, "danger")
        return redirect(url_for("auth.login", next=next_url))

    # SUCCESS
    user.register_successful_login()
    db.session.commit()

    login_user(user, remember=remember)

    if is_safe_redirect(next_url):
        return redirect(next_url)

    return redirect(url_for("browse.browse"))


@auth_bp.post("/logout")
@limiter.limit("10 per minute")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
