"""Run the isolated EvolveEngine service on its own port."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evolve_engine.main import app


def parse_args(argv=None):
    """Parse command-line arguments for EvolveEngine startup."""

    parser = argparse.ArgumentParser(description="EvolveEngine service")
    parser.add_argument("--host", default=os.getenv("EVOLVE_HOST", "127.0.0.1"), help="EvolveEngine host")
    parser.add_argument("--port", type=int, default=int(os.getenv("EVOLVE_PORT", "6062")), help="EvolveEngine port")
    return parser.parse_args(argv)


def main(argv=None):
    """Start the isolated evolution HTTP service."""

    args = parse_args(argv)
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
