from __future__ import annotations

from flask import Blueprint, Response, abort

from .. import limiter
from ..security import auth_required
from ..utils import safe_path
from ..logging import setup_logging

logger = setup_logging()

media_bp = Blueprint("media", __name__)


@media_bp.route("/media/<path:rel_path>")
@limiter.limit("600 per minute")
@auth_required
def media(rel_path: str):
    logger.debug(f"Media file request: {rel_path}")

    # 1) Existenz + innerhalb MEDIA_ROOT prüfen (dein safe_path ist gut)
    _ = safe_path(rel_path)

    # 2) URL-Pfad für nginx-Redirect härten (Windows + Traversal)
    rel = rel_path.lstrip("/").replace("\\", "/")
    if not rel or "/../" in f"/{rel}/" or "/./" in f"/{rel}/":
        abort(404)

    logger.info(f"X-Accel serving media file: {rel}")

    # 3) nginx intern ausliefern lassen
    resp = Response(status=200)
    resp.headers["X-Accel-Redirect"] = f"/_protected_media/{rel}"
    return resp
