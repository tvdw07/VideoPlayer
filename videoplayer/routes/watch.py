from __future__ import annotations
from pathlib import Path
from flask import Blueprint, render_template

from .. import config, limiter
from ..utils import next_video, get_parent_path, get_breadcrumbs
from ..logging import setup_logging

logger = setup_logging()

watch_bp = Blueprint("watch", __name__)


@watch_bp.route("/watch/<path:rel_path>")
@limiter.limit("10 per minute")
def watch(rel_path: str):
    logger.debug(f"Watch request for video: {rel_path}")

    # Check the files against the whitelist
    if not any(rel_path.lower().endswith(ext) for ext in config.VIDEO_EXTENSIONS):
        logger.warning(f"Attempt to watch unsupported file type: {rel_path}")
        return "Unsupported file type", 400

    next_ep = next_video(rel_path)
    parent = get_parent_path(rel_path)
    filename = Path(rel_path).name
    breadcrumbs = get_breadcrumbs(parent)

    logger.debug(f"Playing video: {filename}")
    return render_template(
        "watch.html",
        video=rel_path,
        filename=filename,
        parent=parent,
        next_video=next_ep,
        breadcrumbs=breadcrumbs,
    )

