"""Constitutional ecosystem runtime — charter drift fusion and governed adoption (Stage 12 / Release 43)."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.constitutional_ecosystem_registry import CHARTER_VERSION, adopted_charters, save_adopted_charter
from src.culture_of_beings_registry import adopted_norms
from src.culture_of_beings_runtime import validate_norm_against_identity_narrative_agency_social_and_pacts
from src.multi_being_continuity_registry import adopted_pacts

DRIFT_VERSION = "ecosystem_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_charter_against_upstream_layers(
    charter: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Reject charters violating upstream layers or with insufficient pact evidence."""
    as_norm = {"summary": str(charter.get("summary") or ""), "norm_kind": "mesh_cluster"}
    norm_check = validate_norm_against_identity_narrative_agency_social_and_pacts(as_norm, repo_root=repo_root)
    violations = list(norm_check.get("violations") or [])
    pact_ids = list(charter.get("admitted_pact_ids") or [])
    if len(pact_ids) < 2:
        violations.append("insufficient_admitted_pacts")
    lowered = str(charter.get("summary") or "").lower()
    if "override jarvis" in lowered or "autonomous rewrite" in lowered:
        violations.append("forbidden_charter_language")
    aligned = norm_check.get("aligned") and len(violations) == 0
    return {
        "aligned": aligned,
        "violations": violations,
        "claim_label": "asserted" if aligned else "rejected",
    }


class ConstitutionalEcosystemRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "ecosystem_charter_candidates"
        self._overlay_path = self._runtime_dir / "jarvis_memory_board_ecosystem.v1.json"
        self._lock = threading.Lock()

    def observe_ecosystem_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        drift_events: list[dict[str, Any]] = []
        try:
            pacts = adopted_pacts(repo_root=self._repo_root)
        except Exception:
            pacts = []
        try:
            norms = adopted_norms(repo_root=self._repo_root)
        except Exception:
            norms = []

        if len(pacts) < 2:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="pact_posture",
                    summary=f"Only {len(pacts)} adopted pact(s); charter evidence insufficient",
                )
            )

        candidates = self.surface_charter_candidates()
        for item in self.candidates_from_pact_clusters():
            candidates.append(item)

        for candidate in candidates:
            self._persist_candidate(candidate)

        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).isoformat()
            scope = str(session_id) if session_id else "global"
            for row in operator_decision_ledger_store.list_events(scope, since=since, limit=300):
                kind = str(row.get("decision_kind") or "")
                if kind in {"ecosystem_drift", "multi_being_arbitration", "culture_of_beings_adoption"}:
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
            "cec_class": "CEC-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "adopted_pact_count": len(pacts),
            "adopted_norm_count": len(norms),
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": f"Ecosystem drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_ecosystem_drift_ledger(session_id, result)
        return result

    def _drift_event(self, *, severity: str, source: str, summary: str) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"edrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "cec_class": "CEC-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_charter_candidates(self) -> list[dict[str, Any]]:
        try:
            pacts = adopted_pacts(repo_root=self._repo_root)
        except Exception:
            pacts = []
        if len(pacts) < 2:
            return []
        pact_ids = [str(p.get("pact_id")) for p in pacts[:4] if p.get("pact_id")]
        candidate = self._build_candidate(
            summary=f"Federated cluster charter spanning {len(pact_ids)} adopted pacts",
            charter_kind="federated_cluster",
            admitted_pact_ids=pact_ids,
            admitted_norm_ids=[str(n.get("norm_id")) for n in adopted_norms(repo_root=self._repo_root)[:4]],
            arbitration_policy="operator_supervised",
            stability_score=0.8,
        )
        validation = validate_charter_against_upstream_layers(candidate, repo_root=self._repo_root)
        if validation.get("aligned"):
            return [candidate]
        return []

    def candidates_from_pact_clusters(self) -> list[dict[str, Any]]:
        try:
            pacts = adopted_pacts(repo_root=self._repo_root)
        except Exception:
            return []
        if len(pacts) < 2:
            return []
        by_kind: dict[str, list[str]] = {}
        for pact in pacts:
            kind = str(pact.get("pact_kind") or "bilateral_organism")
            by_kind.setdefault(kind, []).append(str(pact.get("pact_id") or ""))
        candidates: list[dict[str, Any]] = []
        for kind, ids in by_kind.items():
            if len(ids) < 2:
                continue
            candidate = self._build_candidate(
                summary=f"Charter for {kind} cluster ({len(ids)} pacts)",
                charter_kind="bilateral_mesh" if kind == "bilateral_organism" else "federated_cluster",
                admitted_pact_ids=ids,
                admitted_norm_ids=[],
                arbitration_policy="digest_verified_first",
                stability_score=0.85,
            )
            validation = validate_charter_against_upstream_layers(candidate, repo_root=self._repo_root)
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def _build_candidate(self, **fields: Any) -> dict[str, Any]:
        return {
            "charter_version": CHARTER_VERSION,
            "candidate_id": f"ecand_{uuid4().hex[:12]}",
            "member_organism_refs": [],
            "invariant_set": [{"text": "Jarvis must authorize execution paths", "maturity": "constitutional"}],
            "evidence_refs": [f"pact:{pid}" for pid in fields.get("admitted_pact_ids", [])[:4]],
            "digest_verified": False,
            "claim_label": "asserted",
            "operator_promoted": False,
            "cec_class": "CEC-1",
            **fields,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"ecand_{uuid4().hex[:12]}")
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

    def rank_ecosystem_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_ecosystem_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()

        def score(item: dict[str, Any]) -> float:
            base = float(item.get("stability_score") or 0)
            base += len(item.get("admitted_pact_ids") or []) * 2.0
            if lowered and lowered in str(item.get("summary") or "").lower():
                base += 2.0
            return base

        return sorted(candidates, key=score, reverse=True)[:8]

    def adopt_ecosystem_charter(
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

        validation = validate_charter_against_upstream_layers(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {"outcome": "blocked", "reason": "alignment_validation_failed", "violations": validation.get("violations")}

        charter_id = f"charter_{uuid4().hex[:12]}"
        charter = {
            "charter_version": CHARTER_VERSION,
            "charter_id": charter_id,
            "charter_kind": str(candidate.get("charter_kind") or "federated_cluster"),
            "member_organism_refs": list(candidate.get("member_organism_refs") or []),
            "admitted_pact_ids": list(candidate.get("admitted_pact_ids") or []),
            "admitted_norm_ids": list(candidate.get("admitted_norm_ids") or []),
            "invariant_set": list(candidate.get("invariant_set") or []),
            "arbitration_policy": str(candidate.get("arbitration_policy") or "operator_supervised"),
            "summary": str(candidate.get("summary") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "stability_score": float(candidate.get("stability_score") or 0),
            "digest_verified": bool(candidate.get("digest_verified")),
            "claim_label": "asserted",
            "operator_promoted": True,
            "cec_class": "CEC-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_charter(charter, repo_root=self._repo_root)
        self._write_ecosystem_slot(charter)
        self._emit_ecosystem_adoption_ledger(session_id, charter)
        return {"outcome": "adopted", "charter": charter, "cec_class": "CEC-2"}

    def _write_ecosystem_slot(self, charter: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._overlay_path.is_file():
                try:
                    payload = json.loads(self._overlay_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            charters = list(payload.get("adopted_charters") or [])
            charters = [c for c in charters if str(c.get("charter_id")) != str(charter.get("charter_id"))]
            charters.append(charter)
            payload = {
                "ecosystem_overlay_version": "jarvis_memory_board_ecosystem.v1",
                "slot_id": "slot_08",
                "module_id": "capability_ecosystem_v1",
                "adopted_charters": charters,
                "updated_at": _utc_now_iso(),
            }
            self._overlay_path.parent.mkdir(parents=True, exist_ok=True)
            self._overlay_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def ecosystem_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_charters(repo_root=self._repo_root)
        return {
            "candidate_charters": len(candidates),
            "adopted_charters": len(adopted),
            "ecosystem_drift_events": len([c for c in candidates if not c.get("digest_verified")]),
            "member_pact_count": sum(len(c.get("admitted_pact_ids") or []) for c in adopted),
            "claim_label": "asserted",
        }

    def ecosystem_snapshot(self) -> dict[str, Any]:
        return {
            "ecosystem_version": "operator_ecosystem.v1",
            "posture": self.ecosystem_posture(),
            "adopted_charters": adopted_charters(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "claim_label": "asserted",
        }

    def _emit_ecosystem_adoption_ledger(self, session_id: str, charter: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_ecosystem_adoption_event

            append_ecosystem_adoption_event(session_id, charter=charter)
        except Exception:
            pass

    def _emit_ecosystem_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_ecosystem_drift_event

            append_ecosystem_drift_event(session_id, drift=drift)
        except Exception:
            pass


constitutional_ecosystem_runtime = ConstitutionalEcosystemRuntime()
