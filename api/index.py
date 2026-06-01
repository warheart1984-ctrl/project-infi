"""Vercel Python entrypoint for the AAIS Flask app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep preview deployments lightweight by default.
os.environ.setdefault("AAIS_MODEL_MODE", "mock")
os.environ.setdefault("ENVIRONMENT", "production")

from src.api import app  # noqa: E402
