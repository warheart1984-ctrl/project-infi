"""Entrypoint for standalone ARIS service."""

from __future__ import annotations

import uvicorn

from aris_service import create_app


def main() -> None:
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8791, log_level="info")


if __name__ == "__main__":
    main()
