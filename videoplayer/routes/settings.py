from __future__ import annotations
from flask import Blueprint, render_template, current_app, redirect, url_for, request, flash

from .. import limiter
from ..security import auth_required
from ..settings import (
    get_default_per_page,
    get_cleanup_empty_directories,
    set_default_per_page,
    set_cleanup_empty_directories,
)
from ..utils import (
    calculate_media_size,
    format_size,
    get_cached_media_size,
    set_cached_media_size, format_cached_timestamp,
)

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
@limiter.limit("10 per minute")
@auth_required
def index():
    cached = get_cached_media_size(current_app)
    total_bytes = cached["bytes"] if cached else None
    cached_at = format_cached_timestamp(cached["updated_at"]) if cached else None

    try:
        cleanup_enabled = get_cleanup_empty_directories()
        default_per_page = get_default_per_page()
    except RuntimeError as exc:
        flash("Can not load cleanup_enabled and default_per_page", "danger")
        flash("Therefore, using default values for the settings form. You can try to reload this page.", "warning")
        cleanup_enabled = False
        default_per_page = 12

    return render_template(
        "settings.html",
        total_bytes=total_bytes,
        total_formatted=format_size(total_bytes) if total_bytes is not None else None,
        cached_at=cached_at,
        cleanup_enabled=cleanup_enabled,
        default_per_page=default_per_page,
    )


@settings_bp.route("/settings/update", methods=["POST"])
@limiter.limit("5 per minute")
@auth_required
def update_settings():
    cleanup_enabled = request.form.get("cleanup_empty_directories") == "on"
    per_page_raw = (request.form.get("default_per_page") or "").strip()

    try:
        default_per_page = int(per_page_raw)
    except ValueError:
        flash("DEFAULT_PER_PAGE muss eine Zahl sein", "danger")
        return redirect(url_for("settings.index"))

    try:
        set_default_per_page(default_per_page)
        set_cleanup_empty_directories(cleanup_enabled)
    except ValueError as exc:
        message = str(exc).strip() or "Ungültige Einstellungen. Bitte prüfen Sie Ihre Eingaben."
        flash(message, "danger")
        return redirect(url_for("settings.index"))

    flash("Einstellungen gespeichert", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/settings/recalculate", methods=["POST"])
@limiter.limit("5 per minute")
@auth_required
def recalculate():
    total_bytes = calculate_media_size()
    set_cached_media_size(current_app, total_bytes)
    return redirect(url_for("settings.index"))
