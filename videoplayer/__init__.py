from __future__ import annotations
from flask import Flask

from .extensions import csrf
from .config import Config
from .logging import setup_logging
from .routes.browse import browse_bp
from .routes.watch import watch_bp
from .routes.media import media_bp
from .routes.settings import settings_bp


def create_app(config: dict | None = None) -> Flask:
    logger = setup_logging()

    app = Flask(
        __name__,
        template_folder=str(__import__("pathlib").Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(__import__("pathlib").Path(__file__).resolve().parent.parent / "static"),
    )
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    csrf.init_app(app)

    # Blueprints registrieren
    app.register_blueprint(browse_bp)
    app.register_blueprint(watch_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(settings_bp)

    logger.info("Flask application created and configured")
    logger.debug(f"Media root: {app.config.get('MEDIA_ROOT')}" )

    return app
