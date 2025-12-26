from flask import Flask, render_template, send_from_directory, abort, redirect, url_for, flash, Blueprint
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired
from pathlib import Path

BASE_DIR = Path(__file__).parent
MEDIA_ROOT = BASE_DIR / "media"

csrf = CSRFProtect()
main_bp = Blueprint("main", __name__)

VIDEO_EXTENSIONS = {".mp4"}


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
    items = list_dir(rel_path)
    parent = get_parent_path(rel_path)
    breadcrumbs = get_breadcrumbs(rel_path)

    # Für jedes Video ein eigenes Formular mit eigenem CSRF-Token erstellen
    for item in items:
        if item.get('is_video'):
            form = DeleteVideoForm()
            form.video_path.data = item['path']
            item['form'] = form

    return render_template("browse.html",
                           items=items,
                           current=rel_path,
                           parent=parent,
                           breadcrumbs=breadcrumbs)


@main_bp.route("/watch/<path:rel_path>")
def watch(rel_path):
    next_ep = next_video(rel_path)

    parent = get_parent_path(rel_path)

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
    form = DeleteVideoForm()

    if not form.validate_on_submit():
        flash('Ungültiges Formular oder abgelaufener Token', 'danger')
        return redirect(url_for('main.browse'))

    rel_path = form.video_path.data
    if not rel_path:
        abort(400)

    # sichere Auflösung des Pfads
    path = safe_path(rel_path)

    # Prüfungen
    if not path.exists() or not path.is_file():
        flash('Datei nicht gefunden', 'danger')
        parent = get_parent_path(rel_path)
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
    csrf.init_app(app)
    app.register_blueprint(main_bp)
    return app


def start(host="127.0.0.1", port=8000, debug=False):
    create_app().run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=True)
