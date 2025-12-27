from __future__ import annotations
from pathlib import Path
import os

# .env laden
try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH)
except Exception:
    # Falls dotenv nicht installiert ist, läuft die App trotzdem mit OS-ENV/Defaults
    pass

# Projektbasis: Ordner über dem Paket
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Medienstamm: per ENV MEDIA_ROOT überschreibbar, sonst <project>/media
MEDIA_ROOT: Path = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))).resolve()

# Unterstützte Video-Erweiterungen
VIDEO_EXTENSIONS: set[str] = {".mp4"}


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    v = val.strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    return default


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set in environment variables")

    WTF_CSRF_TIME_LIMIT = None

    MEDIA_ROOT = MEDIA_ROOT

    VIDEO_EXTENSIONS = VIDEO_EXTENSIONS

    DEBUG = _env_bool("DEBUG", False)

    RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)