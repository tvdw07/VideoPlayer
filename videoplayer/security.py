from functools import wraps
from flask import current_app, request
from flask_login import current_user
from flask import redirect, url_for
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, InvalidHash


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


_ph = PasswordHasher()

def hash_password(password: str) -> str:
    return _ph.hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except (InvalidHashError, InvalidHash):
        #Add logging here


        # Invalid hash format
        return False