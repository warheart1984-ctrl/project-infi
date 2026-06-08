"""Constitutional evolution runtime — charter amendment drift and governed adoption (Stage 17 / Release 47)."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.constitutional_ecosystem_runtime import validate_charter_against_upstream_layers
from src.constitutional_evolution_registry import AMENDMENT_VERSION, adopted_amendments, save_adopted_amendment

DRIFT_VERSION = "evolution_drift.v1"
TIER5_TAGS = frozenset({"tier5_maturity", "contextual_gate", "dual_gate", "ledger_receipt"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_amendment_against_charter_and_tier5(
    amendment: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    violations: list[str] = []
    charter_id = str(amendment.get("charter_id") or "")
    if not charter_id:
        violations.append("amendment_requires_charter_id")
    as_charter = {
        "summary": str(amendment.get("summary") or ""),
        "admitted_pact_ids": ["pact_a", "pact_b"],
        "charter_id": charter_id or "charter_pending",
    }
    charter_check = validate_charter_against_upstream_layers(as_charter, repo_root=repo_root)
    violations.extend(list(charter_check.get("violations") or []))
    lowered = str(amendment.get("summary") or "").lower()
    if "autonomous rewrite" in lowered or "auto-evolve" in lowered:
        violations.append("forbidden_autonomous_rewrite_language")
    tags = {str(t) for t in (amendment.get("tier5_tags") or [])}
    if not tags.intersection(TIER5_TAGS):
        violations.append("tier5_contextual_gate_tag_required")
    aligned = charter_check.get("aligned") and len(violations) == 0
    return {"aligned": aligned, "violations": violations, "claim_label": "asserted" if aligned else "rejected"}


class ConstitutionalEvolutionRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "charter_amendment_candidates"
        self._overlay_path = self._runtime_dir / "jarvis_memory_board_constitutional_evolution.v1.json"
        self._lock = threading.Lock()

    def observe_evolution_drift(self, *, session_id: str | None = None, window_days: int = 30) -> dict[str, Any]:
        drift_events: list[dict[str, Any]] = []
        try:
            from src.constitutional_ecosystem_registry import adopted_charters

            charters = adopted_charters(repo_root=self._repo_root)
        except Exception:
            charters = []
        if not charters:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="ecosystem_posture",
                    summary="No adopted CEC-2 charters; amendment evidence insufficient",
                )
            )
        candidates = self.surface_amendment_candidates()
        for candidate in candidates:
            self._persist_candidate(candidate)
        result = {
            "outcome": "observed",
            "cev_class": "CEV-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "adopted_charter_count": len(charters),
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": f"Evolution drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_evolution_drift_ledger(session_id, result)
        return result

    def _drift_event(self, *, severity: str, source: str, summary: str) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"evdrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "cev_class": "CEV-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_amendment_candidates(self) -> list[dict[str, Any]]:
        try:
            from src.constitutional_ecosystem_registry import adopted_charters

            charters = adopted_charters(repo_root=self._repo_root)
        except Exception:
            charters = []
        if not charters:
            return []
        charter = charters[0]
        candidate = self._build_candidate(
            summary=f"Tier-5 contextual amendment for charter {charter.get('charter_id', '')[:12]}",
            charter_id=str(charter.get("charter_id") or ""),
            amendment_kind="scope_extension",
            tier5_tags=["tier5_maturity", "contextual_gate", "dual_gate"],
        )
        if validate_amendment_against_charter_and_tier5(candidate, repo_root=self._repo_root).get("aligned"):
            return [candidate]
        return []

    def _build_candidate(self, **fields: Any) -> dict[str, Any]:
        return {
            "amendment_version": AMENDMENT_VERSION,
            "candidate_id": f"amcand_{uuid4().hex[:12]}",
            "evidence_refs": [],
            "claim_label": "asserted",
            "operator_promoted": False,
            "cev_class": "CEV-1",
            **fields,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"amcand_{uuid4().hex[:12]}")
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

    def adopt_charter_amendment(
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
        validation = validate_amendment_against_charter_and_tier5(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {"outcome": "blocked", "reason": "alignment_validation_failed", "violations": validation.get("violations")}
        amendment_id = f"amend_{uuid4().hex[:12]}"
        amendment = {
            "amendment_version": AMENDMENT_VERSION,
            "amendment_id": amendment_id,
            "charter_id": str(candidate.get("charter_id") or ""),
            "amendment_kind": str(candidate.get("amendment_kind") or "composite"),
            "tier5_tags": list(candidate.get("tier5_tags") or []),
            "summary": str(candidate.get("summary") or "")[:500],
            "claim_label": "asserted",
            "operator_promoted": True,
            "cev_class": "CEV-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_amendment(amendment, repo_root=self._repo_root)
        self._write_evolution_overlay(amendment)
        self._emit_amendment_adoption_ledger(session_id, amendment)
        return {"outcome": "adopted", "amendment": amendment, "cev_class": "CEV-2"}

    def _write_evolution_overlay(self, amendment: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._overlay_path.is_file():
                try:
                    payload = json.loads(self._overlay_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            amendments = list(payload.get("adopted_amendments") or [])
            amendments = [a for a in amendments if str(a.get("amendment_id")) != str(amendment.get("amendment_id"))]
            amendments.append(amendment)
            payload = {
                "constitutional_evolution_overlay_version": "jarvis_memory_board_constitutional_evolution.v1",
                "civilizational_tier": 17,
                "module_id": "capability_constitutional_evolution_v1",
                "adopted_amendments": amendments,
                "updated_at": _utc_now_iso(),
            }
            self._overlay_path.parent.mkdir(parents=True, exist_ok=True)
            self._overlay_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def evolution_posture(self) -> dict[str, Any]:
        return {
            "candidate_amendments": len(self.list_candidates(limit=200)),
            "adopted_amendments": len(adopted_amendments(repo_root=self._repo_root)),
            "claim_label": "asserted",
        }

    def evolution_snapshot(self) -> dict[str, Any]:
        return {
            "constitutional_evolution_version": "operator_constitutional_evolution.v1",
            "posture": self.evolution_posture(),
            "adopted_amendments": adopted_amendments(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "claim_label": "asserted",
        }

    def _emit_amendment_adoption_ledger(self, session_id: str, amendment: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_charter_amendment_adoption_event

            append_charter_amendment_adoption_event(session_id, amendment=amendment)
        except Exception:
            pass

    def _emit_evolution_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_evolution_drift_event

            append_evolution_drift_event(session_id, drift=drift)
        except Exception:
            pass


constitutional_evolution_runtime = ConstitutionalEvolutionRuntime()
