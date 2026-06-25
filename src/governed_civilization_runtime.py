"""Governed civilization runtime — civilization drift and governed adoption (Stage 18 / Release 48)."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.constitutional_ecosystem_runtime import validate_charter_against_upstream_layers
from src.governed_civilization_registry import CIVILIZATION_VERSION, adopted_civilizations, save_adopted_civilization
from src.diplomacy.runtime import validate_accord_against_upstream_layers

DRIFT_VERSION = "civilization_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_civilization_against_upstream_envelope(
    civilization: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    violations: list[str] = []
    charter_ids = list(civilization.get("admitted_charter_ids") or [])
    if len(charter_ids) < 2:
        violations.append("civilization_requires_at_least_two_cec_charters")
    as_charter = {
        "summary": str(civilization.get("summary") or ""),
        "admitted_pact_ids": ["pact_a", "pact_b"],
    }
    charter_check = validate_charter_against_upstream_layers(as_charter, repo_root=repo_root)
    violations.extend(list(charter_check.get("violations") or []))
    as_accord = {
        "summary": str(civilization.get("summary") or ""),
        "substrate_scopes": ["ul_substrate", "memory_overlay"],
    }
    accord_check = validate_accord_against_upstream_layers(as_accord, repo_root=repo_root)
    if not accord_check.get("aligned"):
        violations.extend(list(accord_check.get("violations") or []))
    lowered = str(civilization.get("summary") or "").lower()
    if "mutable identity" in lowered or "self-rewrite" in lowered:
        violations.append("forbidden_identity_rewrite_language")
    aligned = charter_check.get("aligned") and len(violations) == 0
    return {"aligned": aligned, "violations": violations, "claim_label": "asserted" if aligned else "rejected"}


class GovernedCivilizationRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "civilization_charter_candidates"
        self._overlay_path = self._runtime_dir / "jarvis_memory_board_civilization.v1.json"
        self._lock = threading.Lock()

    def observe_civilization_drift(self, *, session_id: str | None = None, window_days: int = 30) -> dict[str, Any]:
        drift_events: list[dict[str, Any]] = []
        try:
            from src.constitutional_ecosystem_registry import adopted_charters

            charters = adopted_charters(repo_root=self._repo_root)
        except Exception:
            charters = []
        if len(charters) < 2:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="ecosystem_posture",
                    summary="Insufficient adopted CEC-2 charters for civilization envelope",
                )
            )
        candidates = self.surface_civilization_candidates()
        for candidate in candidates:
            self._persist_candidate(candidate)
        result = {
            "outcome": "observed",
            "gcv_class": "GCV-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "adopted_charter_count": len(charters),
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": f"Civilization drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_civilization_drift_ledger(session_id, result)
        return result

    def _drift_event(self, *, severity: str, source: str, summary: str) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"cvdrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "gcv_class": "GCV-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_civilization_candidates(self) -> list[dict[str, Any]]:
        try:
            from src.constitutional_ecosystem_registry import adopted_charters

            charters = adopted_charters(repo_root=self._repo_root)
        except Exception:
            charters = []
        if len(charters) < 2:
            return []
        candidate = self._build_candidate(
            summary=f"Governed civilization binding charters {charters[0].get('charter_id', '')[:8]} and {charters[1].get('charter_id', '')[:8]}",
            admitted_charter_ids=[str(c.get("charter_id")) for c in charters[:2]],
            admitted_accord_ids=[],
            admitted_treaty_ids=[],
            stability_score=0.88,
        )
        if validate_civilization_against_upstream_envelope(candidate, repo_root=self._repo_root).get("aligned"):
            return [candidate]
        return []

    def _build_candidate(self, **fields: Any) -> dict[str, Any]:
        return {
            "civilization_version": CIVILIZATION_VERSION,
            "candidate_id": f"cvcand_{uuid4().hex[:12]}",
            "evidence_refs": [],
            "claim_label": "asserted",
            "operator_promoted": False,
            "gcv_class": "GCV-1",
            **fields,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"cvcand_{uuid4().hex[:12]}")
        candidate["candidate_id"] = cid
        with self._lock:
            self._candidates_dir.mkdir(parents=True, exist_ok=True)
            (self._candidates_dir / f"{cid}.json").write_text(json.dumps(candidate, sort_keys=True) + "\n", encoding="utf-8")

    def list_candidates(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._candidates_dir.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(self._candidates_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return rows

    def adopt_civilization_charter(
        self,
        candidate: dict[str, Any],
        *,
        operator_approved: bool = False,
        jarvis_authorization: dict[str, Any] | None = None,
        session_id: str = "global",
    ) -> dict[str, Any]:
        if not operator_approved:
            return {"outcome": "blocked", "reason": "operator_approved required", "status": 403}
        auth = dict(jarvis_authorization or {})
        if not auth.get("authorized"):
            return {"outcome": "blocked", "reason": "jarvis_not_authorized", "status": 403}
        validation = validate_civilization_against_upstream_envelope(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {"outcome": "blocked", "reason": "alignment_validation_failed", "violations": validation.get("violations")}
        civilization_id = f"civ_{uuid4().hex[:12]}"
        civilization = {
            "civilization_version": CIVILIZATION_VERSION,
            "civilization_id": civilization_id,
            "admitted_charter_ids": list(candidate.get("admitted_charter_ids") or []),
            "admitted_accord_ids": list(candidate.get("admitted_accord_ids") or []),
            "admitted_treaty_ids": list(candidate.get("admitted_treaty_ids") or []),
            "summary": str(candidate.get("summary") or "")[:500],
            "stability_score": float(candidate.get("stability_score") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "gcv_class": "GCV-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_civilization(civilization, repo_root=self._repo_root)
        self._write_civilization_overlay(civilization)
        self._emit_civilization_adoption_ledger(session_id, civilization)
        return {"outcome": "adopted", "civilization": civilization, "gcv_class": "GCV-2"}

    def _write_civilization_overlay(self, civilization: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._overlay_path.is_file():
                try:
                    payload = json.loads(self._overlay_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            civilizations = list(payload.get("adopted_civilizations") or [])
            civilizations = [
                c for c in civilizations if str(c.get("civilization_id")) != str(civilization.get("civilization_id"))
            ]
            civilizations.append(civilization)
            payload = {
                "civilization_overlay_version": "jarvis_memory_board_civilization.v1",
                "civilizational_tier": 18,
                "module_id": "capability_governed_civilization_v1",
                "adopted_civilizations": civilizations,
                "updated_at": _utc_now_iso(),
            }
            self._overlay_path.parent.mkdir(parents=True, exist_ok=True)
            self._overlay_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def civilization_posture(self) -> dict[str, Any]:
        return {
            "candidate_civilizations": len(self.list_candidates(limit=200)),
            "adopted_civilizations": len(adopted_civilizations(repo_root=self._repo_root)),
            "claim_label": "asserted",
        }

    def civilization_snapshot(self) -> dict[str, Any]:
        return {
            "governed_civilization_version": "operator_civilization.v1",
            "posture": self.civilization_posture(),
            "adopted_civilizations": adopted_civilizations(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "claim_label": "asserted",
        }

    def _emit_civilization_adoption_ledger(self, session_id: str, civilization: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_civilization_adoption_event

            append_civilization_adoption_event(session_id, civilization=civilization)
        except Exception:
            pass

    def _emit_civilization_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_civilization_drift_event

            append_civilization_drift_event(session_id, drift=drift)
        except Exception:
            pass


governed_civilization_runtime = GovernedCivilizationRuntime()
