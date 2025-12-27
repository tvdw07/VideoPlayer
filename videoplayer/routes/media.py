from __future__ import annotations

import werkzeug
from flask import Blueprint, send_file

from .. import limiter
from ..utils import safe_path
from ..logging import setup_logging

logger = setup_logging()

media_bp = Blueprint("media", __name__)


@media_bp.route("/media/<path:rel_path>")
@limiter.limit("10 per minute")
def media(rel_path: str):
    logger.debug(f"Media file request: {rel_path}")
    path = safe_path(rel_path)
    logger.info(f"Serving media file: {rel_path}")
    return send_file(path, conditional=True)

