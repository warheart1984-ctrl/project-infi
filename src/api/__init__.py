"""HTTP API route modules — re-export canonical Flask app from ``src/api.py``."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_MODULE_NAME = "src._api_flask_module"
_API_PATH = Path(__file__).resolve().parent.parent / "api.py"


def _load_api_module():
    if _MODULE_NAME in sys.modules:
        return sys.modules[_MODULE_NAME]
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _API_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Flask API module at {_API_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


_api = _load_api_module()

app = _api.app


def __getattr__(name: str):
    return getattr(_api, name)


__all__ = ["app"]
