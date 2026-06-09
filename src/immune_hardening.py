"""Adaptive immune hardening — scar-tissue thresholds after attacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import json
import math
import os
from pathlib import Path
import threading
from typing import Any

from src.immune_protocol import MAX_DIRECT_SUMMARY_CHARS, RESPONSE_ORDER, ImmuneResponse


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


RESPONSE_FLOOR_LADDER = (
    ImmuneResponse.ALLOW,
    ImmuneResponse.CLAMP,
    ImmuneResponse.REROUTE,
    ImmuneResponse.REJECT,
    ImmuneResponse.QUARANTINE,
)

THREAT_CODE_FLOORS = {
    1: ImmuneResponse.ALLOW,
    2: ImmuneResponse.REJECT,
    3: ImmuneResponse.QUARANTINE,
}


@dataclass
class ThreatMemory:
    threat_code: str
    encounter_count: int = 0
    last_seen_at: str = field(default_factory=_utc_now_iso)
    min_response_floor: str = ImmuneResponse.ALLOW.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "threat_code": self.threat_code,
            "encounter_count": self.encounter_count,
            "last_seen_at": self.last_seen_at,
            "min_response_floor": self.min_response_floor,
        }


@dataclass
class HardeningProfile:
    defense_generation: int = 0
    summary_char_multiplier: float = 1.0
    threat_memory: dict[str, ThreatMemory] = field(default_factory=dict)
    hardened_nodes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "defense_generation": self.defense_generation,
            "summary_char_multiplier": self.summary_char_multiplier,
            "threat_memory": [item.to_dict() for item in self.threat_memory.values()],
            "hardened_nodes": list(self.hardened_nodes),
            "summary_char_limit": self.summary_char_limit(),
            "threat_memory_count": len(self.threat_memory),
        }

    def summary_char_limit(self) -> int:
        scaled = int(MAX_DIRECT_SUMMARY_CHARS * self.summary_char_multiplier)
        return max(120, min(MAX_DIRECT_SUMMARY_CHARS, scaled))

    def min_floor_for_code(self, threat_code: str) -> ImmuneResponse:
        memory = self.threat_memory.get(threat_code)
        if not memory:
            return ImmuneResponse.ALLOW
        floor_value = str(memory.min_response_floor or ImmuneResponse.ALLOW.value)
        try:
            return ImmuneResponse(floor_value)
        except ValueError:
            return ImmuneResponse.ALLOW


class ImmuneHardeningStore:
    """Persist and apply runtime scar-tissue hardening after immune incidents."""

    def __init__(self, runtime_dir: str | Path | None = None):
        base = Path(runtime_dir or _default_runtime_dir())
        self.runtime_dir = base if base.name == "immune-system" else base / "immune-system"
        self._lock = threading.Lock()
        self._profile = HardeningProfile()
        self._load()

    @property
    def _path(self) -> Path:
        return self.runtime_dir / "immune-hardening.json"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            base_dir = Path(runtime_dir)
            self.runtime_dir = (
                base_dir if base_dir.name == "immune-system" else base_dir / "immune-system"
            )
            self._profile = HardeningProfile()
            self._load()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._profile = HardeningProfile()
            self._persist_locked()
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._profile.to_dict()

    def profile_for_protocol(self) -> HardeningProfile:
        with self._lock:
            return HardeningProfile(
                defense_generation=self._profile.defense_generation,
                summary_char_multiplier=self._profile.summary_char_multiplier,
                threat_memory={
                    key: ThreatMemory(
                        threat_code=item.threat_code,
                        encounter_count=item.encounter_count,
                        last_seen_at=item.last_seen_at,
                        min_response_floor=item.min_response_floor,
                    )
                    for key, item in self._profile.threat_memory.items()
                },
                hardened_nodes=list(self._profile.hardened_nodes),
            )

    def record_threat(
        self,
        *,
        threat_code: str,
        severity: str,
        hardened_nodes: list[str] | None = None,
    ) -> dict[str, Any]:
        code = str(threat_code or "unknown_threat").strip() or "unknown_threat"
        with self._lock:
            memory = self._profile.threat_memory.get(code)
            if memory is None:
                memory = ThreatMemory(threat_code=code)
                self._profile.threat_memory[code] = memory
            memory.encounter_count += 1
            memory.last_seen_at = _utc_now_iso()
            floor = THREAT_CODE_FLOORS.get(min(memory.encounter_count, 3), ImmuneResponse.QUARANTINE)
            memory.min_response_floor = floor.value
            for node in hardened_nodes or []:
                node_key = str(node or "").strip().lower()
                if node_key and node_key not in self._profile.hardened_nodes:
                    self._profile.hardened_nodes.append(node_key)
            self._persist_locked()
            return {
                "threat_code": code,
                "encounter_count": memory.encounter_count,
                "min_response_floor": memory.min_response_floor,
                "severity": severity,
            }

    def increment_generation(self, *, reason: str) -> dict[str, Any]:
        with self._lock:
            self._profile.defense_generation += 1
            self._profile.summary_char_multiplier = max(
                0.5,
                0.9 ** self._profile.defense_generation,
            )
            self._persist_locked()
            return {
                "defense_generation": self._profile.defense_generation,
                "summary_char_multiplier": self._profile.summary_char_multiplier,
                "reason": reason,
            }

    def emit_pattern_event(self, *, classification: str, summary: str, severity: str = "S3") -> dict[str, Any] | None:
        try:
            from src.ugr.unified_pattern_ledger import unified_pattern_ledger

            return unified_pattern_ledger.append_pattern_event(
                {
                    "pattern_id": f"immune:hardening:{self._profile.defense_generation}",
                    "event_type": "immune.hardening",
                    "classification": classification,
                    "severity": severity,
                    "summary": summary[:240],
                    "source_payload": {
                        "source": "immune_system",
                        "defense_generation": self._profile.defense_generation,
                    },
                },
                mirror_legacy=False,
            )
        except Exception:
            return None

    def _load(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            threat_memory = {
                str(item.get("threat_code") or "").strip(): ThreatMemory(
                    threat_code=str(item.get("threat_code") or "").strip(),
                    encounter_count=int(item.get("encounter_count") or 0),
                    last_seen_at=str(item.get("last_seen_at") or _utc_now_iso()),
                    min_response_floor=str(item.get("min_response_floor") or ImmuneResponse.ALLOW.value),
                )
                for item in payload.get("threat_memory", [])
                if item.get("threat_code")
            }
            self._profile = HardeningProfile(
                defense_generation=int(payload.get("defense_generation") or 0),
                summary_char_multiplier=float(payload.get("summary_char_multiplier") or 1.0),
                threat_memory=threat_memory,
                hardened_nodes=[
                    str(node).strip().lower()
                    for node in payload.get("hardened_nodes", [])
                    if str(node or "").strip()
                ],
            )
        except Exception:
            self._profile = HardeningProfile()

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._profile.to_dict(), indent=2), encoding="utf-8")


def apply_response_floor(current: ImmuneResponse, floor: ImmuneResponse) -> ImmuneResponse:
    if RESPONSE_ORDER[floor] > RESPONSE_ORDER[current]:
        return floor
    return current


def project_hardening_recommendations(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Project scar-tissue recommendations for OTEM ceiling diagnostic bundles."""
    ctx = dict(context or {})
    snap = immune_hardening.snapshot()
    recommendations: list[dict[str, str]] = []
    if int(snap.get("defense_generation") or 0) > 0:
        recommendations.append(
            {
                "action": "maintain_summary_cap",
                "rationale": "defense generation elevated after prior incidents",
            }
        )
    if int(snap.get("threat_memory_count") or 0) > 0:
        recommendations.append(
            {
                "action": "enforce_threat_floor",
                "rationale": "repeat threat codes retain elevated response floors",
            }
        )
    if not recommendations:
        recommendations.append(
            {
                "action": "baseline_hardening",
                "rationale": "no scar tissue yet; apply standard post-ceiling enrollment",
            }
        )
    return {
        "status": "ok",
        "defense_generation": snap.get("defense_generation", 0),
        "summary_char_limit": snap.get("summary_char_limit"),
        "hardened_nodes": list(snap.get("hardened_nodes") or []),
        "threat_memory_count": int(snap.get("threat_memory_count") or 0),
        "recommendations": recommendations,
        "context": ctx,
    }


def enroll_post_ceiling_hardening(decision: str, *, scope_id: str | None = None) -> dict[str, Any]:
    """Increment defense generation and emit pattern ledger event after ceiling decision."""
    normalized = str(decision or "").strip().lower() or "unknown"
    reason = f"otem_ceiling:{normalized}"
    generation = immune_hardening.increment_generation(reason=reason)
    pattern_event = immune_hardening.emit_pattern_event(
        classification="otem_ceiling_hardening",
        summary=f"Post-ceiling hardening after {normalized} (scope={scope_id or 'global'})",
        severity="S2",
    )
    return {
        "decision": normalized,
        "scope_id": scope_id,
        "generation": generation,
        "pattern_event": pattern_event,
    }


immune_hardening = ImmuneHardeningStore()
