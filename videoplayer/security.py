from functools import wraps
from flask import current_app, request, abort
from flask_login import current_user
from flask import redirect, url_for
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, InvalidHash, HashingError
from .logging import setup_logging

logger = setup_logging()

def auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_app.config.get("AUTH_ENABLED", True):
            return view(*args, **kwargs)

        if current_user.is_authenticated:
            return view(*args, **kwargs)

        # preserve next
        return redirect(url_for("auth.login", next=request.full_path))
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


_ph = PasswordHasher()

def hash_password(password: str) -> str:
    try:
        return _ph.hash(password)
    except HashingError as e:
        raise RuntimeError("Password hashing failed due to an internal error") from e

def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except (InvalidHashError, InvalidHash):
        logger.warning("Password verification failed due to invalid hash format")
        # Invalid hash format
        return False