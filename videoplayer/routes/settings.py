from __future__ import annotations
from flask import Blueprint, render_template, current_app, redirect, url_for

from .. import limiter
from ..utils import (
    calculate_media_size,
    format_size,
    get_cached_media_size,
    set_cached_media_size,
)

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
@limiter.limit("10 per minute")
def index():
    cached = get_cached_media_size(current_app)
    total_bytes = cached["bytes"] if cached else None

    return render_template(
        "settings.html",
        total_bytes=total_bytes,
        total_formatted=format_size(total_bytes) if total_bytes is not None else None,
        cached_at=cached["updated_at"] if cached else None,
    )


@settings_bp.route("/settings/recalculate", methods=["POST"])
@limiter.limit("5 per minute")
def recalculate():
    total_bytes = calculate_media_size()
    set_cached_media_size(current_app, total_bytes)
    return redirect(url_for("settings.index"))
