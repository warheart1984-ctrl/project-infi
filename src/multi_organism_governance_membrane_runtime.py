"""Multi-organism governance membrane runtime — permeability drift and governed adoption (Stage 13 / Release 44)."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.constitutional_ecosystem_registry import adopted_charters
from src.constitutional_ecosystem_runtime import validate_charter_against_upstream_layers
from src.multi_organism_governance_membrane_registry import POLICY_VERSION, adopted_policies, save_adopted_policy

DRIFT_VERSION = "membrane_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_policy_against_upstream_layers(
    policy: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    as_charter = {"summary": str(policy.get("summary") or ""), "admitted_pact_ids": ["pact_a", "pact_b"]}
    charter_check = validate_charter_against_upstream_layers(as_charter, repo_root=repo_root)
    violations = list(charter_check.get("violations") or [])
    lowered = str(policy.get("summary") or "").lower()
    if "bypass otem" in lowered or "bypass ugr" in lowered:
        violations.append("forbidden_execution_bypass_language")
    aligned = charter_check.get("aligned") and len(violations) == 0
    return {"aligned": aligned, "violations": violations, "claim_label": "asserted" if aligned else "rejected"}


class MultiOrganismGovernanceMembraneRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "membrane_policy_candidates"
        self._overlay_path = self._runtime_dir / "jarvis_memory_board_governance_membrane.v1.json"
        self._lock = threading.Lock()

    def observe_membrane_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        drift_events: list[dict[str, Any]] = []
        try:
            charters = adopted_charters(repo_root=self._repo_root)
        except Exception:
            charters = []
        if not charters:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="ecosystem_posture",
                    summary="No adopted ecosystem charters; membrane policy evidence insufficient",
                )
            )

        candidates = self.surface_policy_candidates()
        for candidate in candidates:
            self._persist_candidate(candidate)

        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).isoformat()
            scope = str(session_id) if session_id else "global"
            for row in operator_decision_ledger_store.list_events(scope, since=since, limit=300):
                kind = str(row.get("decision_kind") or "")
                if kind in {"membrane_drift", "ecosystem_adoption", "multi_being_adoption"}:
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
            "mgm_class": "MGM-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "adopted_charter_count": len(charters),
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": f"Membrane drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_membrane_drift_ledger(session_id, result)
        return result

    def _drift_event(self, *, severity: str, source: str, summary: str) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"mdrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "mgm_class": "MGM-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_policy_candidates(self) -> list[dict[str, Any]]:
        try:
            charters = adopted_charters(repo_root=self._repo_root)
        except Exception:
            charters = []
        if not charters:
            return []
        charter = charters[0]
        candidate = self._build_candidate(
            summary=f"Composite permeability policy for charter {charter.get('charter_id', '')[:12]}",
            policy_kind="composite",
            charter_ref={"charter_id": charter.get("charter_id")},
            permitted_channels=["memory_cues", "exchange_envelope", "mesh_handoff", "ledger_federation"],
            consent_requirements={"dual_consent": True, "digest_verified_preferred": True},
            stability_score=0.85,
        )
        validation = validate_policy_against_upstream_layers(candidate, repo_root=self._repo_root)
        if validation.get("aligned"):
            return [candidate]
        return []

    def _build_candidate(self, **fields: Any) -> dict[str, Any]:
        return {
            "policy_version": POLICY_VERSION,
            "candidate_id": f"pcand_{uuid4().hex[:12]}",
            "evidence_refs": [],
            "claim_label": "asserted",
            "operator_promoted": False,
            "mgm_class": "MGM-1",
            **fields,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"pcand_{uuid4().hex[:12]}")
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

    def rank_membrane_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_membrane_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()
        return sorted(
            candidates,
            key=lambda item: float(item.get("stability_score") or 0)
            + (2.0 if lowered and lowered in str(item.get("summary") or "").lower() else 0),
            reverse=True,
        )[:8]

    def adopt_membrane_policy(
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

        validation = validate_policy_against_upstream_layers(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {"outcome": "blocked", "reason": "alignment_validation_failed", "violations": validation.get("violations")}

        policy_id = f"policy_{uuid4().hex[:12]}"
        policy = {
            "policy_version": POLICY_VERSION,
            "policy_id": policy_id,
            "policy_kind": str(candidate.get("policy_kind") or "composite"),
            "charter_ref": dict(candidate.get("charter_ref") or {}),
            "permitted_channels": list(candidate.get("permitted_channels") or []),
            "consent_requirements": dict(candidate.get("consent_requirements") or {}),
            "summary": str(candidate.get("summary") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "stability_score": float(candidate.get("stability_score") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "mgm_class": "MGM-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_policy(policy, repo_root=self._repo_root)
        self._write_membrane_slot(policy)
        self._emit_membrane_adoption_ledger(session_id, policy)
        return {"outcome": "adopted", "policy": policy, "mgm_class": "MGM-2"}

    def _write_membrane_slot(self, policy: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._overlay_path.is_file():
                try:
                    payload = json.loads(self._overlay_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            policies = list(payload.get("adopted_policies") or [])
            policies = [p for p in policies if str(p.get("policy_id")) != str(policy.get("policy_id"))]
            policies.append(policy)
            payload = {
                "governance_membrane_overlay_version": "jarvis_memory_board_governance_membrane.v1",
                "slot_id": "slot_10",
                "module_id": "capability_governance_membrane_v1",
                "adopted_policies": policies,
                "updated_at": _utc_now_iso(),
            }
            self._overlay_path.parent.mkdir(parents=True, exist_ok=True)
            self._overlay_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def check_memory_permeability(self, metadata: dict[str, Any] | None = None) -> bool:
        """MGM-2 consult — allow memory board attach when no policy or channel permitted."""
        policies = adopted_policies(repo_root=self._repo_root)
        if not policies:
            return True
        for policy in policies:
            channels = list(policy.get("permitted_channels") or [])
            if "memory_cues" in channels or policy.get("policy_kind") == "composite":
                return True
        return bool(metadata and metadata.get("federated_session"))

    def check_exchange_permeability(self, envelope: dict[str, Any]) -> dict[str, Any]:
        """IMXP wrapper check — fail-closed when policy blocks exchange."""
        policies = adopted_policies(repo_root=self._repo_root)
        if not policies:
            return {"allowed": True, "reason": "no_policy_default_allow"}
        for policy in policies:
            channels = list(policy.get("permitted_channels") or [])
            if "exchange_envelope" not in channels and policy.get("policy_kind") != "composite":
                continue
            consent = dict(policy.get("consent_requirements") or {})
            if consent.get("dual_consent") and not envelope.get("consent_id"):
                return {"allowed": False, "reason": "dual_consent_required"}
            return {"allowed": True, "reason": "policy_permits_exchange", "policy_id": policy.get("policy_id")}
        return {"allowed": False, "reason": "no_matching_policy"}

    def membrane_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_policies(repo_root=self._repo_root)
        return {
            "candidate_policies": len(candidates),
            "adopted_policies": len(adopted),
            "membrane_drift_events": len(candidates),
            "permeability_channels": len({c for p in adopted for c in (p.get("permitted_channels") or [])}),
            "claim_label": "asserted",
        }

    def membrane_snapshot(self) -> dict[str, Any]:
        return {
            "governance_membrane_version": "operator_governance_membrane.v1",
            "posture": self.membrane_posture(),
            "adopted_policies": adopted_policies(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "claim_label": "asserted",
        }

    def _emit_membrane_adoption_ledger(self, session_id: str, policy: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_membrane_adoption_event

            append_membrane_adoption_event(session_id, policy=policy)
        except Exception:
            pass

    def _emit_membrane_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_membrane_drift_event

            append_membrane_drift_event(session_id, drift=drift)
        except Exception:
            pass


multi_organism_governance_membrane_runtime = MultiOrganismGovernanceMembraneRuntime()
