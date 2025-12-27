from __future__ import annotations
from videoplayer import create_app


def main():
    app = create_app()
    app.run(host=app.config.get("HOST"), port=app.config.get("PORT"), debug=app.config.get("DEBUG"))


if __name__ == "__main__":
    main()

