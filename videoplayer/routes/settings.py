from __future__ import annotations
from pathlib import Path
from flask import Blueprint, render_template, current_app, redirect, url_for, request, flash

from .. import limiter
from ..config import Config
from ..utils import (
    calculate_media_size,
    format_size,
    get_cached_media_size,
    set_cached_media_size, format_cached_timestamp,
)

settings_bp = Blueprint("settings", __name__)


def _read_env_lines(env_path: Path) -> list[str]:
    if not env_path.exists():
        return []
    return env_path.read_text(encoding="utf-8").splitlines()


def _set_env_value(lines: list[str], key: str, value: str) -> list[str]:
    new_lines: list[str] = []
    found = False
    prefix = f"{key}="

    for line in lines:
        if line.strip().startswith(prefix):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}")

    return new_lines


def _write_env_lines(env_path: Path, lines: list[str]) -> None:
    # Ensure the file ends with a newline for POSIX-friendly .env files.
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@settings_bp.route("/settings")
@limiter.limit("10 per minute")
def index():
    cached = get_cached_media_size(current_app)
    total_bytes = cached["bytes"] if cached else None
    cached_at = format_cached_timestamp(cached["updated_at"]) if cached else None

    return render_template(
        "settings.html",
        total_bytes=total_bytes,
        total_formatted=format_size(total_bytes) if total_bytes is not None else None,
        cached_at=cached_at,
        cleanup_enabled=Config.CLEANUP_EMPTY_DIRECTORIES,
        default_per_page=Config.DEFAULT_PER_PAGE,
    )


@settings_bp.route("/settings/update", methods=["POST"])
@limiter.limit("5 per minute")
def update_settings():
    cleanup_enabled = request.form.get("cleanup_empty_directories") == "on"
    per_page_raw = (request.form.get("default_per_page") or "").strip()

    try:
        default_per_page = int(per_page_raw)
    except ValueError:
        flash("DEFAULT_PER_PAGE muss eine Zahl sein", "danger")
        return redirect(url_for("settings.index"))

    if default_per_page < 1:
        flash("DEFAULT_PER_PAGE muss >= 1 sein", "danger")
        return redirect(url_for("settings.index"))

    env_path = Config.BASE_DIR / ".env"
    lines = _read_env_lines(env_path)
    lines = _set_env_value(
        lines,
        "CLEANUP_EMPTY_DIRECTORIES",
        "TRUE" if cleanup_enabled else "FALSE",
    )
    lines = _set_env_value(lines, "DEFAULT_PER_PAGE", str(default_per_page))
    _write_env_lines(env_path, lines)

    # Update in-memory config so changes take effect without restart.
    Config.CLEANUP_EMPTY_DIRECTORIES = cleanup_enabled
    Config.DEFAULT_PER_PAGE = default_per_page
    current_app.config["CLEANUP_EMPTY_DIRECTORIES"] = cleanup_enabled
    current_app.config["DEFAULT_PER_PAGE"] = default_per_page

    flash("Einstellungen gespeichert", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/settings/recalculate", methods=["POST"])
@limiter.limit("5 per minute")
def recalculate():
    total_bytes = calculate_media_size()
    set_cached_media_size(current_app, total_bytes)
    return redirect(url_for("settings.index"))
