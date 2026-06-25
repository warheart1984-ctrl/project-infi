"""Forge platform dashboard JSON for operator console."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _wrap_readout(payload: dict[str, Any]) -> dict[str, Any]:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))


def load_forge_platform_dashboard(*, live_checks: bool = False) -> dict[str, Any]:
    """Load Forge platform dashboard JSON (cached gate status by default)."""
    script = _repo_root() / "wolf-cog-os" / "scripts" / "forge-platform-dashboard.py"
    if not script.exists():
        return _wrap_readout(
            {
            "status": "missing",
            "summary": f"dashboard script not found: {script}",
            "runtime_effect": "readout_only",
            "claim_status": "asserted",
            }
        )

    command = [sys.executable, str(script), "--json"]
    if live_checks:
        command.append("--check")

    completed = subprocess.run(
        command,
        cwd=str(_repo_root()),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if completed.returncode not in {0, 1} and not completed.stdout.strip():
        return _wrap_readout(
            {
            "status": "error",
            "summary": (completed.stderr or completed.stdout or "forge dashboard failed").strip()[-400:],
            "runtime_effect": "readonly",
            "claim_status": "asserted",
            }
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _wrap_readout(
            {
            "status": "error",
            "summary": f"invalid dashboard JSON: {exc}",
            "runtime_effect": "readout_only",
            "claim_status": "asserted",
            }
        )

    gates = list(payload.get("gates") or [])
    red_gates = [row for row in gates if row.get("level") == "red"]
    return _wrap_readout(
        {
        "status": "ok",
        "dashboard": payload,
        "summary": f"substrates={payload.get('substrates', {}).get('substrate_count', 0)} gates={len(gates)} red={len(red_gates)}",
        "live_checks": live_checks,
        "runtime_effect": "readout_only",
        "claim_status": "asserted" if red_gates else "proven",
        }
    )
