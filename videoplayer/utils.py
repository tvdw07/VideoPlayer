from __future__ import annotations
from pathlib import Path

from flask import abort
from .config import Config
from natsort import natsorted


def safe_path(rel_path: str = "") -> Path:
    root = Config.MEDIA_ROOT.resolve()

    try:
        path = (root / rel_path).resolve(strict=True)
    except FileNotFoundError:
        abort(404)

    try:
        path.relative_to(root)
    except ValueError:
        abort(404)  # Access outside the allowed area

    return path


def list_dir(rel_path: str = "") -> list[dict]:
    path = safe_path(rel_path)
    if not path.exists() or not path.is_dir():
        abort(404)

    dirs: list[dict] = []
    files: list[dict] = []

    for p in path.iterdir():
        entry = {
            "name": p.name,
            "is_dir": p.is_dir(),
            "is_video": p.is_file() and p.suffix.lower() in Config.VIDEO_EXTENSIONS,
            "path": str(Path(rel_path) / p.name),
        }
        if p.is_dir():
            dirs.append(entry)
        elif p.is_file():
            files.append(entry)

    dirs.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())

    return dirs + files


def next_video(rel_path: str) -> str | None:
    path = safe_path(rel_path)
    parent = path.parent

    videos = [
        p for p in parent.iterdir()
        if p.suffix.lower() in Config.VIDEO_EXTENSIONS
    ]

    videos = natsorted(videos, key=lambda p: p.name)

    try:
        idx = videos.index(path)
    except ValueError:
        return None

    if idx + 1 < len(videos):
        return str(Path(rel_path).parent / videos[idx + 1].name)

    return None



def get_breadcrumbs(rel_path: str) -> list[str]:
    if not rel_path:
        return []
    return list(Path(rel_path).parts)


def get_parent_path(rel_path: str) -> str:
    parent = Path(rel_path).parent
    return "" if parent == Path(".") else str(parent)


def calculate_media_size() -> int:
    """Return total size in bytes of all files under MEDIA_ROOT."""
    return sum(p.stat().st_size for p in Config.MEDIA_ROOT.rglob("*") if p.is_file())


def format_size(num_bytes: int) -> str:
    """Human readable size, base 1024."""
    step = 1024
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < step or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= step
    # Fallback; should not be reached
    return f"{size:.2f} {units[-1]}"


def _media_size_cache_path(app=None) -> Path:
    """Pfad zur Cache-Datei (persistiert im instance folder)."""
    # Import lokal halten, um zirkuläre Imports zu vermeiden
    if app is None:
        from flask import current_app

        app = current_app

    # instance_path existiert bei Flask immer; wir stellen sicher, dass der Ordner existiert.
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)
    return instance_path / "media_size_cache.json"


def get_cached_media_size(app=None) -> dict | None:
    """Liest den gecachten Media-Size-Wert.

    Returns:
        {"bytes": int, "updated_at": str(ISO)} oder None falls nicht vorhanden/ungültig.
    """
    import json

    cache_file = _media_size_cache_path(app)
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        b = data.get("bytes")
        ts = data.get("updated_at")
        if not isinstance(b, int) or b < 0 or not isinstance(ts, str) or not ts:
            return None
        return {"bytes": b, "updated_at": ts}
    except Exception:
        # Bei kaputter Datei lieber "kein Cache" statt harter Fehler.
        return None


def set_cached_media_size(app=None, total_bytes: int = 0) -> None:
    """Schreibt den Media-Size-Cache atomar."""
    import json
    from datetime import datetime, timezone

    if not isinstance(total_bytes, int) or total_bytes < 0:
        raise ValueError("total_bytes must be a non-negative int")

    cache_file = _media_size_cache_path(app)
    tmp = cache_file.with_suffix(cache_file.suffix + ".tmp")

    payload = {
        "bytes": total_bytes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(cache_file)


def cleanup_empty_directories(
    start_path: Path,
    stop_at: Path = Config.MEDIA_ROOT,
) -> int:
    """
    Entfernt rekursiv leere Verzeichnisse von start_path nach oben.

    Returns:
        Anzahl der gelöschten Verzeichnisse
    """
    deleted = 0
    current = start_path

    while current != stop_at:
        if not current.exists() or not current.is_dir():
            break

        try:
            # leer?
            if any(current.iterdir()):
                break

            current.rmdir()
            deleted += 1
        except OSError:
            break

        current = current.parent

    return deleted