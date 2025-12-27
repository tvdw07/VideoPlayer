from __future__ import annotations
from flask import Blueprint, render_template

from ..utils import calculate_media_size, format_size

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def index():
    total_bytes = calculate_media_size()
    return render_template(
        "settings.html",
        total_bytes=total_bytes,
        total_formatted=format_size(total_bytes),
    )

