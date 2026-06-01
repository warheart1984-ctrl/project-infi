"""Run the isolated Forge contractor service on its own port."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from forge.main import app
from forge.config import load_forge_config


def parse_args(argv=None):
    """Parse command-line arguments for Forge startup."""

    config = load_forge_config()
    parser = argparse.ArgumentParser(description="Forge contractor service")
    parser.add_argument("--host", default=config.host, help="Forge host")
    parser.add_argument("--port", type=int, default=config.port, help="Forge port")
    return parser.parse_args(argv)


def main(argv=None):
    """Start the isolated Forge HTTP service."""

    args = parse_args(argv)
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
