"""Shared Jarvis runtime invocation for workflow shell and FastAPI delegation."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any


def _ensure_project_root_on_path() -> None:
    """Best-effort: make sure project root is on sys.path for src.* imports."""
    try:
        here = Path(__file__).resolve()
        root = here
        for _ in range(6):
            if (root / "app" / "main.py").exists() and (root / "src" / "api.py").exists():
                root_str = str(root)
                if root_str not in sys.path:
                    sys.path.insert(0, root_str)
                break
            root = root.parent
    except Exception:
        pass


def _preload_operator_routes() -> None:
    _ensure_project_root_on_path()
    importlib.import_module("src.operator_api_routes")


def invoke_jarvis_compat(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Run the canonical Jarvis compat handler without the WSGI legacy mount."""
    _preload_operator_routes()
    from src.api import app, bootstrap_ai_runtime, jarvis_chat_compat

    bootstrap_ai_runtime(reason="jarvis_runtime_service")
    with app.test_request_context("/api/jarvis", method="POST", json=dict(payload or {})):
        response = jarvis_chat_compat()
    status_code = int(getattr(response, "status_code", 200) or 200)
    body = response.get_json(silent=True) if hasattr(response, "get_json") else None
    return status_code, dict(body or {})


def invoke_legacy_json_post(path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """POST JSON to a Flask route on the canonical runtime app."""
    _preload_operator_routes()
    from src.api import app, bootstrap_ai_runtime

    bootstrap_ai_runtime(reason="jarvis_runtime_service")
    with app.test_request_context(path, method="POST", json=dict(payload or {})):
        response = app.full_dispatch_request()
    status_code = int(getattr(response, "status_code", 200) or 200)
    body = response.get_json(silent=True) if hasattr(response, "get_json") else None
    return status_code, dict(body or {})
