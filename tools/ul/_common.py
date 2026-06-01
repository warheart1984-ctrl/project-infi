"""Shared helpers for the AAIS-UL toolkit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

UL_WRAP_MARKERS = (
    "attach_ul_substrate",
    "wrap_runtime_snapshot",
    "wrap_bridge_result",
    "wrap_pipeline",
    "wrap_capability_result",
    "wrap_modular_preview",
    "wrap_operator_action",
    "wrap_ugr_response",
    "wrap_service_bridge_result",
    "wrap_cloud_forge_bundle",
    "wrap_contractor_payload",
    "build_ul_snapshot",
    "adapt_ingress",
    "ul_substrate",
)

SCAN_SKIP_PARTS = {
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "external",
    "archive",
    "Project-Infinity-main",
    "wolf-cog-os",
}

SCAN_ALLOWLIST_SUFFIXES = (
    "_types.py",
    "schemas.py",
    "datetime_compat.py",
)

SCAN_ALLOWLIST_FILES = {
    "aais_ul.py",
    "aais_ul_substrate.py",
    "mock_ai.py",
    "models.py",
}


def ensure_project_root() -> None:
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def load_json_payload(*, file_path: str | None, inline: str | None) -> Any:
    if inline:
        return json.loads(inline)
    if file_path:
        text = Path(file_path).read_text(encoding="utf-8")
        return json.loads(text)
    if not sys.stdin.isatty():
        text = sys.stdin.read()
        if text.strip():
            return json.loads(text)
    raise ValueError("Provide --file, --json, or pipe JSON on stdin.")


def print_json(payload: Any, *, indent: int = 2) -> None:
    print(json.dumps(payload, indent=indent, sort_keys=True, default=str))


def relative_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
