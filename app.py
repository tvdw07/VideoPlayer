from flask import Flask, render_template, send_from_directory, abort, request, redirect, url_for, flash, Blueprint
from pathlib import Path

BASE_DIR = Path(__file__).parent
MEDIA_ROOT = BASE_DIR / "media"

main_bp = Blueprint("main", __name__)

VIDEO_EXTENSIONS = {".mp4"}


def safe_path(rel_path=""):
    path = (MEDIA_ROOT / rel_path).resolve()
    if not str(path).startswith(str(MEDIA_ROOT.resolve())):
        abort(403)
    return path


def list_dir(rel_path=""):
    path = safe_path(rel_path)
    if not path.exists() or not path.is_dir():
        abort(404)

    items = []
    for p in sorted(path.iterdir()):
        items.append({
            "name": p.name,
            "is_dir": p.is_dir(),
            "is_video": p.suffix.lower() in VIDEO_EXTENSIONS,
            "path": str(Path(rel_path) / p.name)
        })
    return items


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

def get_breadcrumbs(rel_path):
    parts = rel_path.split("/") if rel_path else []
    return parts


@main_bp.route("/")
@main_bp.route("/browse/")
@main_bp.route("/browse/<path:rel_path>")
def browse(rel_path=""):
    items = list_dir(rel_path)
    parent = str(Path(rel_path).parent) if rel_path else None
    breadcrumbs = get_breadcrumbs(rel_path)
    return render_template("browse.html",
                           items=items,
                           current=rel_path,
                           parent=parent,
                           breadcrumbs=breadcrumbs)


@main_bp.route("/watch/<path:rel_path>")
def watch(rel_path):
    next_ep = next_video(rel_path)

    parent = str(Path(rel_path).parent)
    if parent == ".":
        parent = ""

    filename = Path(rel_path).name
    breadcrumbs = get_breadcrumbs(parent)

    return render_template(
        "watch.html",
        video=rel_path,
        filename=filename,
        parent=parent,
        next_video=next_ep,
        breadcrumbs=breadcrumbs
    )


# Neue Route: Datei löschen (sicher, nur per POST)
@main_bp.route('/delete', methods=['POST'])
def delete_video():
    rel_path = request.form.get('video_path')
    if not rel_path:
        abort(400)

    # sichere Auflösung des Pfads
    path = safe_path(rel_path)

    # Prüfungen
    if not path.exists() or not path.is_file():
        flash('Datei nicht gefunden', 'danger')
        parent = str(Path(rel_path).parent)
        if parent == '.':
            parent = ''
        return redirect(url_for('main.browse', rel_path=parent))

    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        abort(400)

    try:
        path.unlink()
        flash('Datei gelöscht', 'success')
    except PermissionError:
        flash('Keine Berechtigung zum Löschen der Datei', 'danger')
    except FileNotFoundError:
        flash('Datei nicht gefunden', 'danger')
    except Exception as e:
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
    path = safe_path(rel_path)
    return send_from_directory(path.parent, path.name)


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
    app.register_blueprint(main_bp)
    return app


def start(host="127.0.0.1", port=8000, debug=False):
    create_app().run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=True)
