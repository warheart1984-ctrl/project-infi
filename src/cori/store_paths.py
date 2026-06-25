"""Resolved paths for CORI Alpha SQLite stores (env-aware)."""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DATA = _PROJECT_ROOT / "data"


def panel_store_path() -> Path:
    override = os.environ.get("NOVA_PANEL_STORE_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DATA / "nova_panel_store.sqlite3"


def continuity_store_path() -> Path:
    override = os.environ.get("CONTINUITY_STORE_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DATA / "continuity.sqlite3"


def law_ledger_path() -> Path:
    override = os.environ.get("LAW_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    # Support both naming conventions under data/
    for candidate in (_DATA / "law-ledger.sqlite3", _DATA / "law_ledger.sqlite3"):
        if candidate.is_file():
            return candidate
    return _DATA / "law-ledger.sqlite3"


def pel_store_path() -> Path:
    override = os.environ.get("PEL_STORE_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DATA / "pel.sqlite3"


def claim_registry_path() -> Path:
    override = os.environ.get("CLAIM_REGISTRY_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DATA / "claim_registry.sqlite3"


def alpha_evidence_path() -> Path:
    override = os.environ.get("ALPHA_EVIDENCE_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DATA / "alpha_evidence.sqlite3"


def vault_store_path() -> Path:
    override = os.environ.get("VAULT_STORE_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DATA / "vault.sqlite3"
