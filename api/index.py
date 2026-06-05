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
for _constitutional_key in ("AAIS_REQUIRE_CONSTITUTIONAL_LAW", "AAIS_REQUIRE_COLLABORATION_CHARTER"):
    os.environ.setdefault(_constitutional_key, "1")

from src.api import app  # noqa: E402
