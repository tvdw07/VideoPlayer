from __future__ import annotations
from videoplayer import create_app


def main():
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=app.config.get("DEBUG"))


if __name__ == "__main__":
    main()

