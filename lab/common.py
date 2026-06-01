"""Shared Lab Console utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_factory.common import ClaimLabel, json_stable, sha256_file, sha256_text, write_json

LAB_VERSION = "lab.v1"
DEFAULT_RUNTIME_ROOT = Path(".runtime/lab")
DEFAULT_LEDGER_PATH = DEFAULT_RUNTIME_ROOT / "lab_ledger.jsonl"

MANIFEST_FILENAME = "LAB_PROJECT_MANIFEST.json"
SPINE_FILENAME = "LAB_SPINE_PROFILE.json"
CAPABILITY_FILENAME = "LAB_CAPABILITY_PROFILE.json"
RECEIPT_FILENAME = "LAB_SESSION_RECEIPT.json"
WORKSPACE_DIRNAME = "workspace"
EXPERIMENTS_DIRNAME = "experiments"
SESSIONS_DIRNAME = "sessions"

SPEC_VERSION = "lab.lab_project_spec.v1"
RECEIPT_VERSION = "lab.lab_session_receipt.v1"
SPINE_VERSION = "lab.lab_spine_profile.v1"
CAPABILITY_VERSION = "lab.lab_capability_profile.v1"

__all__ = [
    "ClaimLabel",
    "CAPABILITY_FILENAME",
    "CAPABILITY_VERSION",
    "DEFAULT_LEDGER_PATH",
    "DEFAULT_RUNTIME_ROOT",
    "EXPERIMENTS_DIRNAME",
    "LAB_VERSION",
    "MANIFEST_FILENAME",
    "RECEIPT_FILENAME",
    "RECEIPT_VERSION",
    "SESSIONS_DIRNAME",
    "SPEC_VERSION",
    "SPINE_FILENAME",
    "SPINE_VERSION",
    "WORKSPACE_DIRNAME",
    "json_stable",
    "sha256_file",
    "sha256_text",
    "write_json",
]
