"""Safety Envelope Organ — read-only threshold snapshot from SWARM_LAW doctrine."""

# Mythic: Safety Envelope
# Engineering: SafetyEnvelopeEngine
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SWARM_LAW_PATH = Path("docs/contracts/SWARM_LAW.md")
SIGNAL_FILENAME = "safety_envelope_signal.v1.json"
SIGNAL_VERSION = "safety_envelope_signal.v1"
HALT_ENV = "AAIS_SAFETY_ENVELOPE_HALT"

DEFAULT_THRESHOLDS = {
    "uncertainty_max": 0.35,
    "comms_degraded": False,
    "halt_required": False,
}


def _runtime_governance_dir(root: Path) -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser() / "governance"
    return root / ".runtime" / "governance"


def load_swarm_law_excerpt(root: Path | None = None) -> str:
    """Return doctrine excerpt for operator display only — not a live halt signal."""
    root = root or Path(__file__).resolve().parents[1]
    path = root / SWARM_LAW_PATH
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    if "safety envelope" in text.lower():
        start = text.lower().index("safety envelope")
        return text[start : start + 400]
    return text[:400]


def _parse_env_halt() -> bool | None:
    raw = os.environ.get(HALT_ENV)
    if raw is None or not str(raw).strip():
        return None
    normalized = str(raw).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def load_halt_signal(*, root: Path | None = None) -> dict[str, Any]:
    """Load governed halt state from explicit runtime signal or env — never doctrine text."""
    root = root or Path(__file__).resolve().parents[1]
    env_halt = _parse_env_halt()
    if env_halt is not None:
        return {
            "signal_version": SIGNAL_VERSION,
            "halt_required": env_halt,
            "source": "env",
            "path": HALT_ENV,
        }

    signal_path = _runtime_governance_dir(root) / SIGNAL_FILENAME
    if signal_path.is_file():
        try:
            payload = json.loads(signal_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "signal_version": SIGNAL_VERSION,
                "halt_required": False,
                "source": "default",
                "path": str(signal_path.relative_to(root)).replace("\\", "/"),
                "error": "invalid_json",
            }
        if payload.get("signal_version") != SIGNAL_VERSION:
            return {
                "signal_version": SIGNAL_VERSION,
                "halt_required": False,
                "source": "default",
                "path": str(signal_path.relative_to(root)).replace("\\", "/"),
                "error": "unsupported_signal_version",
            }
        return {
            "signal_version": SIGNAL_VERSION,
            "halt_required": bool(payload.get("halt_required")),
            "source": "runtime_signal",
            "path": str(signal_path.relative_to(root)).replace("\\", "/"),
            "issuer": payload.get("issuer"),
            "reason": payload.get("reason"),
            "issued_at_utc": payload.get("issued_at_utc"),
        }

    return {
        "signal_version": SIGNAL_VERSION,
        "halt_required": False,
        "source": "default",
    }


def build_envelope_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    thresholds = dict(DEFAULT_THRESHOLDS)
    halt_signal = load_halt_signal(root=root)
    thresholds["halt_required"] = bool(halt_signal.get("halt_required"))
    return {
        "safety_envelope_organ_version": "safety_envelope_organ.v1",
        "envelope_id": "default",
        "thresholds": thresholds,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "source_contract": str(SWARM_LAW_PATH),
        "read_only": True,
    }
