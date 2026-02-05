from __future__ import annotations
from pathlib import Path

from flask import abort
from .config import Config
from natsort import natsorted


def safe_path(rel_path: str = "") -> Path:
    root = Config.MEDIA_ROOT.resolve()
    rel_path = rel_path.lstrip("/").replace("\\", "/")

    try:
        # Resolve to an absolute, existing path and avoid traversal via "..".
        path = (root / rel_path).resolve(strict=True)
    except FileNotFoundError:
        abort(404)

    try:
        # Ensure the resolved path stays within MEDIA_ROOT.
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
            "path": str(Path(rel_path) / p.name).replace("\\", "/"),  # Normalize for URLs
        }
        if p.is_dir():
            dirs.append(entry)
        elif p.is_file():
            files.append(entry)

    # Keep directories first, then files, both case-insensitively sorted.
    dirs.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())

    return dirs + files


def next_video(rel_path: str) -> str | None:
    path = safe_path(rel_path)
    parent = path.parent

    videos = [
        p for p in parent.iterdir()
        if p.is_file() and p.suffix.lower() in Config.VIDEO_EXTENSIONS
    ]

    # Natural sort so "Episode 10" follows "Episode 9".
    videos = natsorted(videos, key=lambda p: p.name)

    try:
        idx = videos.index(path)
    except ValueError:
        return None

    if idx + 1 < len(videos):
        next_path = str(Path(rel_path).parent / videos[idx + 1].name)
        # Normalize for URLs (forward slashes on Windows too).
        return next_path.replace("\\", "/")

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

def format_cached_timestamp(iso_ts: str | None) -> str | None:
    """
    Convert ISO timestamp like '2026-02-02T09:16:17.333766+00:00'
    into something UI-friendly in local time.
    Output: '02.02.2026 · 10:16'
    """
    if not iso_ts:
        return None

    from datetime import datetime

    try:
        dt = datetime.fromisoformat(iso_ts)
        # If timezone-aware, convert to local time; if naive, leave as is
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return dt.strftime("%d.%m.%Y · %H:%M")
    except ValueError:
        return None



def _media_size_cache_path(app=None) -> Path:
    """Path to the cache file (persistent in the instance folder)."""
    # Keep imports local to avoid circular imports
    if app is None:
        from flask import current_app

        app = current_app

    # instance_path always exists in Flask; we ensure that the folder exists.
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)
    return instance_path / "media_size_cache.json"


def get_cached_media_size(app=None) -> dict | None:
    """
    Reads the cached media size value.

    Returns:
        {‘bytes’: int, ‘updated_at’: str(ISO)} or None if not available/invalid.
    """
    import json

    cache_file = _media_size_cache_path(app)
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        cached_bytes = data.get("bytes")
        updated_at_str = data.get("updated_at")
        if (
            not isinstance(cached_bytes, int)
            or cached_bytes < 0
            or not isinstance(updated_at_str, str)
            or not updated_at_str
        ):
            return None
        return {"bytes": cached_bytes, "updated_at": updated_at_str}
    except Exception:
        # If the cache file is corrupted, return None
        return None


def set_cached_media_size(app=None, total_bytes: int = 0) -> None:
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

    # Write to a temp file and atomically replace to avoid partial writes.
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(cache_file)


def cleanup_empty_directories(
    start_path: Path,
    stop_at: Path = Config.MEDIA_ROOT,
) -> int:
    """
    Recursively removes empty directories from start_path upwards.

    Returns:
        Number of directories deleted
    """
    deleted = 0
    current = start_path

    while current != stop_at:
        if not current.exists() or not current.is_dir():
            break

        try:
            # Stop at the first non-empty directory.
            if any(current.iterdir()):
                break

            current.rmdir()
            deleted += 1
        except OSError:
            break

        current = current.parent

    return deleted


def clamp_pagination_params(page: int | str | None) -> int:

    try:
        page_i = int(page)
    except (TypeError, ValueError):
        page_i = 1

    if page_i < 1:
        page_i = 1

    return page_i


def paginate_list(items: list, page: int, per_page: int | None = None) -> dict:
    if per_page is None:
        per_page = Config.DEFAULT_PER_PAGE

    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)

    # If page > pages: clamp to last page
    if page > pages:
        page = pages

    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
        "prev_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < pages else None,
    }
