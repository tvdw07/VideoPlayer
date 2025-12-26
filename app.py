from flask import Flask, render_template, abort, redirect, url_for, flash, Blueprint, send_file
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired
from pathlib import Path
import logging
import logging.handlers

BASE_DIR = Path(__file__).parent
MEDIA_ROOT = BASE_DIR / "media"

csrf = CSRFProtect()
main_bp = Blueprint("main", __name__)

VIDEO_EXTENSIONS = {".mp4"}


def setup_logging(log_file=None, log_level=logging.INFO):
    """
    Konfiguriere ein strukturiertes Logging-System.

    Args:
        log_file: Pfad zur Log-Datei (optional). Wenn None, nur Console-Logging.
        log_level: Logging-Level (default: INFO)
    """
    logger = logging.getLogger("videoplayer")
    logger.setLevel(log_level)

    # Verhindere doppeltes Logging bei mehrfachem Aufruf
    if logger.hasHandlers():
        return logger

    # Format für Log-Meldungen
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler (Standard Output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (nur wenn log_file angegeben)
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5  # Behalte 5 alte Log-Dateien
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Initialisiere Logger (Console nur, kein Log-File)
logger = setup_logging()


class DeleteVideoForm(FlaskForm):
    """Form für sicheres Löschen von Videos mit CSRF-Protection."""
    video_path = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Löschen")


# ...existing code...


def safe_path(rel_path=""):
    try:
        path = (MEDIA_ROOT / rel_path).resolve()
        path.relative_to(MEDIA_ROOT.resolve())
        return path
    except ValueError:
        abort(403)



def list_dir(rel_path: str = ""):
    path = safe_path(rel_path)
    if not path.exists() or not path.is_dir():
        abort(404)

    dirs = []
    files = []

    for p in path.iterdir():
        entry = {
            "name": p.name,
            "is_dir": p.is_dir(),
            "is_video": p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS,
            "path": str(Path(rel_path) / p.name)
        }

        if p.is_dir():
            dirs.append(entry)
        elif p.is_file():
            files.append(entry)

    # Ordner zuerst, dann Dateien – jeweils sortiert
    dirs.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())

    return dirs + files



def next_video(rel_path):
    path = safe_path(rel_path)
    parent = path.parent
    videos = [p for p in sorted(parent.iterdir())
              if p.suffix.lower() in VIDEO_EXTENSIONS]

    if path in videos:
        idx = videos.index(path)
        if idx + 1 < len(videos):
            return str(Path(rel_path).parent / videos[idx + 1].name)

    return None

def get_breadcrumbs(rel_path: str):
    if not rel_path:
        return []
    return list(Path(rel_path).parts)

def get_parent_path(rel_path: str) -> str:
    parent = Path(rel_path).parent
    return "" if parent == Path(".") else str(parent)




@main_bp.route("/")
@main_bp.route("/browse/")
@main_bp.route("/browse/<path:rel_path>")
def browse(rel_path=""):
    logger.debug(f"Browse request for path: {rel_path or 'root'}")
    try:
        items = list_dir(rel_path)
        parent = get_parent_path(rel_path)
        breadcrumbs = get_breadcrumbs(rel_path)

        # Für jedes Video ein eigenes Formular mit eigenem CSRF-Token erstellen
        for item in items:
            if item.get('is_video'):
                form = DeleteVideoForm()
                form.video_path.data = item['path']
                item['form'] = form

        logger.debug(f"Listed {len(items)} items in {rel_path or 'root'}")
        return render_template("browse.html",
                               items=items,
                               current=rel_path,
                               parent=parent,
                               breadcrumbs=breadcrumbs)
    except Exception as e:
        logger.error(f"Error in browse for path '{rel_path}': {str(e)}", exc_info=True)
        raise


@main_bp.route("/watch/<path:rel_path>")
def watch(rel_path):
    logger.debug(f"Watch request for video: {rel_path}")
    try:
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
            breadcrumbs=breadcrumbs
        )
    except Exception as e:
        logger.error(f"Error in watch for video '{rel_path}': {str(e)}", exc_info=True)
        raise


# Neue Route: Datei löschen (sicher, nur per POST)
@main_bp.route('/delete', methods=['POST'])
def delete_video():
    form = DeleteVideoForm()

    if not form.validate_on_submit():
        logger.warning("Delete attempt with invalid CSRF token or form data")
        flash('Ungültiges Formular oder abgelaufener Token', 'danger')
        return redirect(url_for('main.browse'))

    rel_path = form.video_path.data
    if not rel_path:
        logger.warning("Delete attempt with empty video_path")
        abort(400)

    # sichere Auflösung des Pfads
    path = safe_path(rel_path)

    # Prüfungen
    if not path.exists() or not path.is_file():
        logger.warning(f"Delete attempt for non-existent file: {rel_path}")
        flash('Datei nicht gefunden', 'danger')
        parent = get_parent_path(rel_path)
        return redirect(url_for('main.browse', rel_path=parent))

    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        logger.warning(f"Delete attempt for non-video file: {rel_path}")
        abort(400)

    try:
        logger.info(f"Deleting video: {rel_path}")
        path.unlink()
        logger.info(f"Successfully deleted: {rel_path}")
        flash('Datei gelöscht', 'success')
    except PermissionError:
        logger.error(f"Permission denied when deleting: {rel_path}")
        flash('Keine Berechtigung zum Löschen der Datei', 'danger')
    except FileNotFoundError:
        logger.error(f"File not found during deletion: {rel_path}")
        flash('Datei nicht gefunden', 'danger')
    except Exception as e:
        logger.error(f"Error deleting file '{rel_path}': {str(e)}", exc_info=True)
        flash('Fehler beim Löschen der Datei', 'danger')

    parent = str(path.parent.relative_to(MEDIA_ROOT))
    if parent == '.':
        parent = ''
    return redirect(url_for('main.browse', rel_path=parent))


def calculate_media_size():
    """Return total size in bytes of all files under MEDIA_ROOT."""
    return sum(p.stat().st_size for p in MEDIA_ROOT.rglob('*') if p.is_file())


def format_size(num_bytes: int) -> str:
    """Human readable size, base 1024."""
    step = 1024
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < step or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= step


@main_bp.route("/media/<path:rel_path>")
def media(rel_path):
    logger.debug(f"Media file request: {rel_path}")
    try:
        path = safe_path(rel_path)
        logger.info(f"Serving media file: {rel_path}")
        return send_file(path, conditional=True)
    except Exception as e:
        logger.error(f"Error serving media file '{rel_path}': {str(e)}", exc_info=True)
        raise



@main_bp.route("/settings")
def settings():
    total_bytes = calculate_media_size()
    return render_template(
        "settings.html",
        total_bytes=total_bytes,
        total_formatted=format_size(total_bytes),
    )


def create_app(config: dict | None = None):
    app = Flask(__name__)
    app.secret_key = "dev-change-this"
    if config:
        app.config.update(config)
    csrf.init_app(app)
    app.register_blueprint(main_bp)

    logger.info("Flask application created and configured")
    logger.debug(f"Media root: {MEDIA_ROOT}")

    return app


def start(host="127.0.0.1", port=8000, debug=False):
    logger.info(f"Starting application on {host}:{port} (debug={debug})")
    create_app().run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    logger.info("Application startup initiated")
    create_app().run(host="0.0.0.0", port=8000, debug=True)
