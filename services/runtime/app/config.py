"""Service base URLs for the runtime mesh orchestrator."""

from __future__ import annotations

import os


def _url(name: str, default: str) -> str:
    override = os.environ.get(name, "").strip().rstrip("/")
    return override or default


IDENTITY_URL = _url("RUNTIME_IDENTITY_URL", "http://identity:8000/v1")
ASSET_URL = _url("RUNTIME_ASSET_URL", "http://asset:8000/v1")
EVIDENCE_URL = _url("RUNTIME_EVIDENCE_URL", "http://evidence:8000/v1")
VALIDATION_URL = _url("RUNTIME_VALIDATION_URL", "http://validation:8000/v1")
AUDIT_URL = _url("RUNTIME_AUDIT_URL", "http://runtime:8000/v1")
