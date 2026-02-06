from __future__ import annotations

from .extensions import db
from .models import AppSetting

# hard whitelist
_ALLOWED = {"DEFAULT_PER_PAGE", "CLEANUP_EMPTY_DIRECTORIES"}

def _require(key: str) -> AppSetting:
    if key not in _ALLOWED:
        raise ValueError(f"Setting {key!r} is not allowed")
    row = db.session.get(AppSetting, key)
    if row is None:
        raise RuntimeError(f"Missing required setting in DB: {key}")
    return row

def _get_or_create(key: str) -> AppSetting:
    if key not in _ALLOWED:
        raise ValueError(f"Setting {key!r} is not allowed")
    row = db.session.get(AppSetting, key)
    if row is None:
        row = AppSetting(key=key)
        db.session.add(row)
    return row

# ---------- DEFAULT_PER_PAGE ----------
def get_default_per_page() -> int:
    row = _require("DEFAULT_PER_PAGE")
    if row.int_value is None:
        raise RuntimeError("DEFAULT_PER_PAGE exists but int_value is NULL")
    return int(row.int_value)

def set_default_per_page(value: int) -> int:
    iv = int(value)
    if iv < 1:
        raise ValueError("DEFAULT_PER_PAGE must be >= 1")
    if iv > 200:
        raise ValueError("DEFAULT_PER_PAGE must be <= 200")
    row = _get_or_create("DEFAULT_PER_PAGE")
    row.int_value = iv
    row.bool_value = None
    db.session.commit()
    return iv

# ---------- CLEANUP_EMPTY_DIRECTORIES ----------
def get_cleanup_empty_directories() -> bool:
    row = _require("CLEANUP_EMPTY_DIRECTORIES")
    if row.bool_value is None:
        raise RuntimeError("CLEANUP_EMPTY_DIRECTORIES exists but bool_value is NULL")
    return bool(row.bool_value)

def set_cleanup_empty_directories(value: bool | str | int) -> bool:
    if isinstance(value, bool):
        bv = value
    else:
        s = str(value).strip().lower()
        bv = s in {"1", "true", "yes", "on"}
    row = _get_or_create("CLEANUP_EMPTY_DIRECTORIES")
    row.bool_value = bv
    row.int_value = None
    db.session.commit()
    return bv
