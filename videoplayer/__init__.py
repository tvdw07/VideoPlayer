from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, redirect, request, url_for, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import csrf, limiter, db, migrate, login_manager
from .config import Config
from .logging import setup_logging
from .models import User
from .routes.admin import admin_bp
from .routes.auth import auth_bp

from .routes.browse import browse_bp
from .routes.health import health_bp
from .routes.watch import watch_bp
from .routes.media import media_bp
from .routes.settings import settings_bp
from sqlalchemy import text


def create_app(config: dict | None = None) -> Flask:
    logger = setup_logging()

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    # Ensure instance folder exists (SQLite, caches, etc.)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Hard safety guard: never run unauthenticated in production by accident
    if not app.config.get("DEBUG", False) and not app.config.get("AUTH_ENABLED", True):
        raise RuntimeError("Refusing to start with AUTH_ENABLED=0 while DEBUG=0")

    # Extensions
    logger.info("Initializing extensions")
    csrf.init_app(app)
    logger.info("CSRF protection initialized")

    storage_uri = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    if (not app.config.get("DEBUG", False)) and (not app.config.get("TESTING", False)) and storage_uri.startswith("memory://"):
        logger.warning("RATELIMIT_STORAGE_URI=memory:// in production is unsafe. Use Redis.")
        raise RuntimeError("In production, RATELIMIT_STORAGE_URI must not be memory:// (use Redis).")

    limiter.storage_uri = storage_uri
    limiter.enabled = app.config.get("RATE_LIMIT_ENABLED", True)
    limiter.init_app(app)
    logger.info("Rate limiting initialized")

    db.init_app(app)
    logger.info("Database initialized")
    migrate.init_app(app, db)
    logger.info("Database migrations initialized")

    with app.app_context():
        ensure_default_values_in_db()
        logger.info("Default values ensured in database")

    login_manager.init_app(app)
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    # Unauthorized behavior
    if app.config.get("AUTH_ENABLED", True):
        login_manager.login_view = "auth.login"

        @login_manager.unauthorized_handler
        def _unauthorized():
            return redirect(url_for("auth.login", next=request.path))
    else:
        logger.warning("AUTH_ENABLED is False: authentication is DISABLED")
        login_manager.login_view = None

    logger.info("Login manager initialized")

    from .cli import create_user
    app.cli.add_command(create_user)

    # Blueprints
    logger.info("Registering blueprints")
    app.register_blueprint(browse_bp)
    app.register_blueprint(watch_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)
    logger.info("Blueprints registered")

    # Security headers
    @app.after_request
    def set_security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

        # --- CSP (start with Report-Only) ---
        csp = (
            "default-src 'self'; "
            "base-uri 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://vjs.zencdn.net; "
            "script-src 'self' https://vjs.zencdn.net; "
            "media-src 'self'; "
            "connect-src 'self'; "
            "upgrade-insecure-requests"
        )

        # Report-Only first (safe rollout)
        resp.headers.setdefault("Content-Security-Policy", csp)

        if not app.config.get("DEBUG", False) and request.is_secure:
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

        return resp

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        try:
            db.session.rollback()
        except Exception:
            pass
        return render_template("errors/500.html"), 500

    logger.info("Flask application created and configured")
    logger.debug(f"Media root: {app.config.get('MEDIA_ROOT')}" )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    return app


def ensure_default_values_in_db() -> None:
    # Skip if table not yet present (first run before db upgrade)
    try:
        db.session.execute(text("SELECT 1 FROM app_settings LIMIT 1"))
    except Exception:
        db.session.rollback()
        return

    db.session.execute(text("""
        INSERT INTO app_settings (key, int_value, bool_value, updated_at)
        VALUES ('DEFAULT_PER_PAGE', 12, NULL, NOW())
        ON CONFLICT (key) DO NOTHING
    """))
    db.session.execute(text("""
        INSERT INTO app_settings (key, int_value, bool_value, updated_at)
        VALUES ('CLEANUP_EMPTY_DIRECTORIES', NULL, FALSE, NOW())
        ON CONFLICT (key) DO NOTHING
    """))
    db.session.commit()