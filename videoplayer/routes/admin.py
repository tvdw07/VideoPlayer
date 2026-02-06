from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select

from ..extensions import db, limiter
from ..models import User
from ..security import auth_required, admin_required, hash_password

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
@limiter.limit("30/minute")
@auth_required
@admin_required
def index():
    return redirect(url_for("admin.users"))


@admin_bp.get("/users")
@limiter.limit("30/minute")
@auth_required
@admin_required
def users():
    rows = db.session.execute(select(User).order_by(User.id.asc())).scalars().all()
    return render_template("admin/users.html", users=rows)


@admin_bp.get("/users/new")
@limiter.limit("15/minute")
@auth_required
@admin_required
def users_new():
    return render_template("admin/user_new.html")


@admin_bp.post("/users/new")
@limiter.limit("10/minute")
@auth_required
@admin_required
def users_create():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    is_admin = request.form.get("is_admin") == "on"
    is_active = request.form.get("is_active") == "on"

    # validation
    if not (3 <= len(username) <= 64):
        flash("Username must be between 3 and 64 characters.", "error")
        return redirect(url_for("admin.users_new"))

    if len(password) < 12:
        flash("Password must be at least 12 characters.", "error")
        return redirect(url_for("admin.users_new"))

    exists = db.session.execute(select(User.id).where(User.username == username)).scalar_one_or_none()
    if exists is not None:
        flash("Username already exists.", "error")
        return redirect(url_for("admin.users_new"))

    u = User(
        username=username,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=is_active,
    )
    db.session.add(u)
    db.session.commit()

    flash(f"User '{username}' created.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.post("/users/<int:user_id>/toggle-active")
@limiter.limit("20/minute")
@auth_required
@admin_required
def user_toggle_active(user_id: int):
    u = db.session.get(User, user_id)
    if u is None:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    # avoid locking yourself out
    if u.id == getattr(request, "user", None):
        pass

    u.is_active = not u.is_active
    db.session.commit()
    flash(f"User '{u.username}' active={u.is_active}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.post("/users/<int:user_id>/toggle-admin")
@limiter.limit("20/minute")
@auth_required
@admin_required
def user_toggle_admin(user_id: int):
    u = db.session.get(User, user_id)
    if u is None:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    # prevent removing your own admin accidentally
    from flask_login import current_user
    if u.id == current_user.id:
        flash("You cannot remove admin from yourself.", "error")
        return redirect(url_for("admin.users"))

    u.is_admin = not u.is_admin
    db.session.commit()
    flash(f"User '{u.username}' admin={u.is_admin}.", "success")
    return redirect(url_for("admin.users"))

