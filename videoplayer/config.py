from __future__ import annotations
from pathlib import Path
import os
from videoplayer.logging import setup_logging

logger = setup_logging()
# load .env
try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH)
except Exception:
    # IF dotenv is not installed or .env file does not exist, skip loading and use default values
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

    # Projekt-Root-Dir
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    logger.info(f"BASE_DIR: {BASE_DIR}")

    # Mediaroot: overridable via ENV MEDIA_ROOT, else <project>/media
    MEDIA_ROOT: Path = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))).resolve()
    logger.info(f"MEDIA_ROOT: {MEDIA_ROOT}")

    if not MEDIA_ROOT.exists():
        logger.warning("MEDIA_ROOT does not exist")
        MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        logger.debug("Created MEDIA_ROOT")

    # Supported video file extensions
    VIDEO_EXTENSIONS: set[str] = {".mp4"}
    logger.info(f"Supported video extensions: {VIDEO_EXTENSIONS}")

    WTF_CSRF_TIME_LIMIT = int(os.getenv("WTF_CSRF_TIME_LIMIT", "3600"))
    logger.info(f"CSRF token time limit is set to: {WTF_CSRF_TIME_LIMIT}")

    DEBUG = _env_bool("DEBUG", False)
    logger.info(f"DEBUG: {DEBUG}")

    RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)
    logger.info(f"RATE_LIMIT_ENABLED: {RATE_LIMIT_ENABLED}")

    # --- Auth feature flag ---
    AUTH_ENABLED = _env_bool("AUTH_ENABLED", True)

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'instance' / 'app.db').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Session/Cookie security (prod defaults) ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    # In Prod MUSS Secure True sein (requires HTTPS)
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", not DEBUG)

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = _env_bool("REMEMBER_COOKIE_SECURE", not DEBUG)