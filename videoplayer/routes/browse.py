from __future__ import annotations
from flask import Blueprint, render_template, redirect, url_for, flash

from ..forms import DeleteVideoForm
from ..utils import (
    list_dir,
    get_parent_path,
    get_breadcrumbs,
    safe_path,
)
from ..config import MEDIA_ROOT, VIDEO_EXTENSIONS
from ..logging import setup_logging

logger = setup_logging()

browse_bp = Blueprint("browse", __name__)


@browse_bp.route("/")
@browse_bp.route("/browse/")
@browse_bp.route("/browse/<path:rel_path>")
def browse(rel_path: str = ""):
    logger.debug(f"Browse request for path: {rel_path or 'root'}")
    items = list_dir(rel_path)
    parent = get_parent_path(rel_path)
    breadcrumbs = get_breadcrumbs(rel_path)



    # For every video, create a separate form with its own CSRF token and remove non-video files
    for item in items:
        if item.get("is_video"):
            form = DeleteVideoForm()
            form.video_path.data = item["path"]
            item["form"] = form


    logger.debug(f"Listed {len(items)} items in {rel_path or 'root'}")
    return render_template(
        "browse.html", items=items, current=rel_path, parent=parent, breadcrumbs=breadcrumbs
    )


@browse_bp.route("/delete", methods=["POST"])
def delete_video():
    form = DeleteVideoForm()

    if not form.validate_on_submit():
        logger.warning("Delete attempt with invalid CSRF token or form data")
        flash("Invalid Form", "danger")
        return redirect(url_for("browse.browse"))

    rel_path = form.video_path.data
    if not rel_path:
        logger.warning("Delete attempt with empty video_path")
        return redirect(url_for("browse.browse")), 400

    path = safe_path(rel_path)

    if not path.exists() or not path.is_file():
        logger.warning(f"Delete attempt for non-existent file: {rel_path}")
        flash("Datei nicht gefunden", "danger")
        parent = get_parent_path(rel_path)
        return redirect(url_for("browse.browse", rel_path=parent))

    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        logger.warning(f"Delete attempt for non-video file: {rel_path}")
        return redirect(url_for("browse.browse")), 400

    try:
        logger.info(f"Deleting video: {rel_path}")
        path.unlink()
        logger.info(f"Successfully deleted: {rel_path}")
        flash("Datei gelöscht", "success")
    except PermissionError:
        logger.error(f"Permission denied when deleting: {rel_path}")
        flash("Keine Berechtigung zum Löschen der Datei", "danger")
    except FileNotFoundError:
        logger.error(f"File not found during deletion: {rel_path}")
        flash("Datei nicht gefunden", "danger")
    except Exception as e:
        logger.error(f"Error deleting file '{rel_path}': {str(e)}", exc_info=True)
        flash("Fehler beim Löschen der Datei", "danger")

    parent = str(path.parent.relative_to(MEDIA_ROOT))
    if parent == ".":
        parent = ""
    return redirect(url_for("browse.browse", rel_path=parent))
