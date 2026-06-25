"""Inter-substrate diplomacy runtime — cross-substrate drift and governed adoption (Stage 15 / Release 45)."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.human_ai_charter_surfaces import attach_charter_surfaces
from src.diplomacy.registry import ACCORD_VERSION, adopted_accords, save_adopted_accord
from src.multi_organism_governance_membrane_runtime import validate_policy_against_upstream_layers

DRIFT_VERSION = "substrate_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_accord_against_upstream_layers(
    accord: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Reject accords that violate MGM/CEC upstream or forbid execution bypass."""
    as_policy = {
        "summary": str(accord.get("summary") or ""),
        "policy_kind": "composite",
        "permitted_channels": list(accord.get("substrate_scopes") or ["memory_cues", "exchange_envelope"]),
    }
    policy_check = validate_policy_against_upstream_layers(as_policy, repo_root=repo_root)
    violations = list(policy_check.get("violations") or [])
    lowered = str(accord.get("summary") or "").lower()
    if "bypass otem" in lowered or "bypass ugr" in lowered or "unsigned handoff" in lowered:
        violations.append("forbidden_execution_bypass_language")
    aligned = policy_check.get("aligned") and len(violations) == 0
    return {"aligned": aligned, "violations": violations, "claim_label": "asserted" if aligned else "rejected"}


class InterSubstrateDiplomacyRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "diplomatic_accord_candidates"
        self._overlay_path = self._runtime_dir / "jarvis_memory_board_diplomacy.v1.json"
        self._lock = threading.Lock()

    def observe_substrate_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        drift_events: list[dict[str, Any]] = []
        try:
            from src.multi_organism_governance_membrane_registry import adopted_policies

            policies = adopted_policies(repo_root=self._repo_root)
        except Exception:
            policies = []
        if not policies:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="membrane_posture",
                    summary="No adopted membrane policies; diplomatic accord evidence insufficient",
                )
            )

        candidates = self.surface_accord_candidates()
        for candidate in candidates:
            self._persist_candidate(candidate)

        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).isoformat()
            scope = str(session_id) if session_id else "global"
            for row in operator_decision_ledger_store.list_events(scope, since=since, limit=300):
                kind = str(row.get("decision_kind") or "")
                if kind in {"substrate_drift", "membrane_adoption", "diplomatic_adoption"}:
                    drift_events.append(
                        self._drift_event(
                            severity="nominal",
                            source=f"ledger:{kind}",
                            summary=str(row.get("summary") or "")[:120],
                        )
                    )
        except Exception:
            pass

        result = {
            "outcome": "observed",
            "isd_class": "ISD-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "adopted_policy_count": len(policies),
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": f"Substrate drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        result = attach_charter_surfaces(
            result,
            domain="inter_substrate_diplomacy",
            declared_scopes=["ul_substrate", "memory_overlay", "imxp_envelope", "operator_ledger"],
            drift_events=drift_events,
            upstream_evidence_count=len(policies),
            candidates=candidates,
        )
        if session_id:
            self._emit_substrate_drift_ledger(session_id, result)
        return result

    def _drift_event(self, *, severity: str, source: str, summary: str) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"sdrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "isd_class": "ISD-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_accord_candidates(self) -> list[dict[str, Any]]:
        try:
            from src.multi_organism_governance_membrane_registry import adopted_policies

            policies = adopted_policies(repo_root=self._repo_root)
        except Exception:
            policies = []
        if not policies:
            return []
        policy = policies[0]
        candidate = self._build_candidate(
            summary=f"Diplomatic accord for membrane policy {policy.get('policy_id', '')[:12]}",
            accord_kind="composite",
            policy_ref={"policy_id": policy.get("policy_id")},
            substrate_scopes=["ul_substrate", "memory_overlay", "imxp_envelope", "operator_ledger"],
            consent_requirements={"dual_consent": True, "charter_aligned": True},
            stability_score=0.82,
        )
        validation = validate_accord_against_upstream_layers(candidate, repo_root=self._repo_root)
        if validation.get("aligned"):
            return [candidate]
        return []

    def _build_candidate(self, **fields: Any) -> dict[str, Any]:
        return {
            "accord_version": ACCORD_VERSION,
            "candidate_id": f"acand_{uuid4().hex[:12]}",
            "evidence_refs": [],
            "claim_label": "asserted",
            "operator_promoted": False,
            "isd_class": "ISD-1",
            **fields,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"acand_{uuid4().hex[:12]}")
        candidate["candidate_id"] = cid
        with self._lock:
            self._candidates_dir.mkdir(parents=True, exist_ok=True)
            (self._candidates_dir / f"{cid}.json").write_text(
                json.dumps(candidate, sort_keys=True) + "\n", encoding="utf-8"
            )

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

    def rank_diplomacy_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_substrate_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()
        return sorted(
            candidates,
            key=lambda item: float(item.get("stability_score") or 0)
            + (2.0 if lowered and lowered in str(item.get("summary") or "").lower() else 0),
            reverse=True,
        )[:8]

    def adopt_diplomatic_accord(
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

        validation = validate_accord_against_upstream_layers(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {"outcome": "blocked", "reason": "alignment_validation_failed", "violations": validation.get("violations")}

        accord_id = f"accord_{uuid4().hex[:12]}"
        accord = {
            "accord_version": ACCORD_VERSION,
            "accord_id": accord_id,
            "accord_kind": str(candidate.get("accord_kind") or "composite"),
            "policy_ref": dict(candidate.get("policy_ref") or {}),
            "charter_ref": dict(candidate.get("charter_ref") or {}),
            "substrate_scopes": list(candidate.get("substrate_scopes") or []),
            "consent_requirements": dict(candidate.get("consent_requirements") or {}),
            "summary": str(candidate.get("summary") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "stability_score": float(candidate.get("stability_score") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "isd_class": "ISD-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_accord(accord, repo_root=self._repo_root)
        self._write_diplomacy_overlay(accord)
        self._emit_diplomatic_adoption_ledger(session_id, accord)
        return {"outcome": "adopted", "accord": accord, "isd_class": "ISD-2"}

    def _write_diplomacy_overlay(self, accord: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._overlay_path.is_file():
                try:
                    payload = json.loads(self._overlay_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            accords = list(payload.get("adopted_accords") or [])
            accords = [a for a in accords if str(a.get("accord_id")) != str(accord.get("accord_id"))]
            accords.append(accord)
            payload = {
                "diplomacy_overlay_version": "jarvis_memory_board_diplomacy.v1",
                "civilizational_tier": 15,
                "module_id": "capability_inter_substrate_diplomacy_v1",
                "adopted_accords": accords,
                "updated_at": _utc_now_iso(),
            }
            self._overlay_path.parent.mkdir(parents=True, exist_ok=True)
            self._overlay_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def diplomacy_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_accords(repo_root=self._repo_root)
        return {
            "candidate_accords": len(candidates),
            "adopted_accords": len(adopted),
            "substrate_drift_events": len(candidates),
            "substrate_scopes": len({s for a in adopted for s in (a.get("substrate_scopes") or [])}),
            "claim_label": "asserted",
        }

    def diplomacy_snapshot(self) -> dict[str, Any]:
        adopted = adopted_accords(repo_root=self._repo_root)
        candidates = self.list_candidates(limit=20)
        drift_events: list[dict[str, Any]] = []
        try:
            from src.multi_organism_governance_membrane_registry import adopted_policies

            policy_count = len(adopted_policies(repo_root=self._repo_root))
        except Exception:
            policy_count = 0
        if not adopted and not candidates:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="diplomacy_posture",
                    summary="No adopted accords or candidates; epistemic perimeter bounded to registry scopes only",
                )
            )
        payload = {
            "inter_substrate_diplomacy_version": "operator_diplomacy.v1",
            "posture": self.diplomacy_posture(),
            "adopted_accords": adopted,
            "recent_candidates": candidates,
            "claim_label": "asserted",
        }
        return attach_charter_surfaces(
            payload,
            domain="inter_substrate_diplomacy",
            declared_scopes=["ul_substrate", "memory_overlay", "imxp_envelope", "operator_ledger"],
            drift_events=drift_events,
            upstream_evidence_count=policy_count,
            candidates=candidates,
        )

    def _emit_diplomatic_adoption_ledger(self, session_id: str, accord: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_diplomatic_adoption_event

            append_diplomatic_adoption_event(session_id, accord=accord)
        except Exception:
            pass

    def _emit_substrate_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_substrate_drift_event

            append_substrate_drift_event(session_id, drift=drift)
        except Exception:
            pass


inter_substrate_diplomacy_runtime = InterSubstrateDiplomacyRuntime()
