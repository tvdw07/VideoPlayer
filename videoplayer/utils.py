from __future__ import annotations
from pathlib import Path

from flask import abort
from .config import Config


def safe_path(rel_path: str = "") -> Path:
    try:
        path = (Config.MEDIA_ROOT / rel_path).resolve()
        path.relative_to(Config.MEDIA_ROOT.resolve())
        return path
    except ValueError:
        abort(403)


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
    videos = [p for p in sorted(parent.iterdir()) if p.suffix.lower() in Config.VIDEO_EXTENSIONS]

    if path in videos:
        idx = videos.index(path)
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