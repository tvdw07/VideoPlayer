from __future__ import annotations
from pathlib import Path
import os
from videoplayer.logging import setup_logging

logger = setup_logging()
# .env laden
try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH)
except Exception:
    # Falls dotenv nicht installiert ist, läuft die App trotzdem mit OS-ENV/Defaults
    pass


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

    # Projektbasis: Ordner über dem Paket
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    logger.info(f"BASE_DIR: {BASE_DIR}")

    # Medienstamm: per ENV MEDIA_ROOT überschreibbar, sonst <project>/media
    MEDIA_ROOT: Path = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))).resolve()
    logger.info(f"MEDIA_ROOT: {MEDIA_ROOT}")

    if not MEDIA_ROOT.exists():
        logger.warning("MEDIA_ROOT does not exist")
        MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        logger.debug("Created MEDIA_ROOT")

    # Unterstützte Video-Erweiterungen
    VIDEO_EXTENSIONS: set[str] = {".mp4"}
    logger.info(f"Supported video extensions: {VIDEO_EXTENSIONS}")

    WTF_CSRF_TIME_LIMIT = None
    logger.info(f"CSRF token time limit is set to: {WTF_CSRF_TIME_LIMIT}")

    DEBUG = _env_bool("DEBUG", False)
    logger.info(f"DEBUG: {DEBUG}")

    RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)
    logger.info(f"RATE_LIMIT_ENABLED: {RATE_LIMIT_ENABLED}")

    CLEANUP_EMPTY_DIRECTORIES = _env_bool("CLEANUP_EMPTY_DIRECTORIES", False)
    logger.info(f"CLEANUP_EMPTY_DIRECTORIES: {CLEANUP_EMPTY_DIRECTORIES}")

    HOST = os.getenv("HOST", "localhost").strip()
    allowed_hosts = {"localhost", "0.0.0.0", "127.0.0.1"}
    if HOST not in allowed_hosts:
        raise ValueError("HOST must be either 'localhost', '0.0.0.0', or '127.0.0.1'")
    logger.info(f"HOST: {HOST}")

    PORT = int(os.getenv("PORT", "5000"))
    if not (1 <= PORT <= 65535):
        raise ValueError("PORT must be an integer between 1 and 65535")
    logger.info(f"PORT: {PORT}")