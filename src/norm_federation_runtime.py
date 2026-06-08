"""Norm federation runtime — treaty drift fusion and governed adoption (Stage 16 / Release 46)."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.human_ai_charter_surfaces import attach_charter_surfaces
from src.culture_of_beings_runtime import validate_norm_against_identity_narrative_agency_social_and_pacts
from src.norm_federation_registry import TREATY_VERSION, adopted_treaties, save_adopted_treaty

DRIFT_VERSION = "norm_federation_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_treaty_against_norms_charters_and_membrane(
    treaty: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    violations: list[str] = []
    norm_ids = list(treaty.get("adopted_norm_ids") or [])
    if len(norm_ids) < 2:
        violations.append("treaty_requires_at_least_two_adopted_norm_ids")
    lowered = str(treaty.get("summary") or "").lower()
    if "auto-promote norm" in lowered or "bypass jarvis" in lowered:
        violations.append("forbidden_auto_promotion_language")
    as_norm = {"summary": str(treaty.get("summary") or ""), "norm_kind": "cluster"}
    norm_check = validate_norm_against_identity_narrative_agency_social_and_pacts(as_norm, repo_root=repo_root)
    violations.extend(list(norm_check.get("violations") or []))
    aligned = norm_check.get("aligned") and len(violations) == 0
    return {"aligned": aligned, "violations": violations, "claim_label": "asserted" if aligned else "rejected"}


class NormFederationRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "norm_federation_candidates"
        self._overlay_path = self._runtime_dir / "jarvis_memory_board_norm_federation.v1.json"
        self._lock = threading.Lock()

    def observe_federation_drift(self, *, session_id: str | None = None, window_days: int = 30) -> dict[str, Any]:
        drift_events: list[dict[str, Any]] = []
        try:
            from src.culture_of_beings_registry import adopted_norms

            norms = adopted_norms(repo_root=self._repo_root)
        except Exception:
            norms = []
        if len(norms) < 2:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="culture_of_beings_posture",
                    summary="Insufficient adopted COB-2 norms for federation treaty evidence",
                )
            )
        candidates = self.surface_treaty_candidates()
        for candidate in candidates:
            self._persist_candidate(candidate)
        result = {
            "outcome": "observed",
            "nfd_class": "NFD-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "adopted_norm_count": len(norms),
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": f"Federation drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        result = attach_charter_surfaces(
            result,
            domain="norm_federation",
            declared_scopes=["cob_2_norms", "charter_refs", "membrane_envelope", "operator_ledger"],
            drift_events=drift_events,
            upstream_evidence_count=len(norms),
            candidates=candidates,
        )
        if session_id:
            self._emit_federation_drift_ledger(session_id, result)
        return result

    def _drift_event(self, *, severity: str, source: str, summary: str) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"nfdrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "nfd_class": "NFD-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_treaty_candidates(self) -> list[dict[str, Any]]:
        try:
            from src.culture_of_beings_registry import adopted_norms

            norms = adopted_norms(repo_root=self._repo_root)
        except Exception:
            norms = []
        if len(norms) < 2:
            return []
        candidate = self._build_candidate(
            summary=f"Federation treaty linking norms {norms[0].get('norm_id', '')[:8]} and {norms[1].get('norm_id', '')[:8]}",
            treaty_kind="cluster_norm",
            adopted_norm_ids=[str(n.get("norm_id")) for n in norms[:2]],
            stability_score=0.8,
        )
        if validate_treaty_against_norms_charters_and_membrane(candidate, repo_root=self._repo_root).get("aligned"):
            return [candidate]
        return []

    def _build_candidate(self, **fields: Any) -> dict[str, Any]:
        return {
            "treaty_version": TREATY_VERSION,
            "candidate_id": f"tcand_{uuid4().hex[:12]}",
            "evidence_refs": [],
            "claim_label": "asserted",
            "operator_promoted": False,
            "nfd_class": "NFD-1",
            **fields,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"tcand_{uuid4().hex[:12]}")
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

    def adopt_federation_treaty(
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
        validation = validate_treaty_against_norms_charters_and_membrane(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {"outcome": "blocked", "reason": "alignment_validation_failed", "violations": validation.get("violations")}
        treaty_id = f"treaty_{uuid4().hex[:12]}"
        treaty = {
            "treaty_version": TREATY_VERSION,
            "treaty_id": treaty_id,
            "treaty_kind": str(candidate.get("treaty_kind") or "cluster_norm"),
            "adopted_norm_ids": list(candidate.get("adopted_norm_ids") or []),
            "charter_refs": list(candidate.get("charter_refs") or []),
            "summary": str(candidate.get("summary") or "")[:500],
            "stability_score": float(candidate.get("stability_score") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "nfd_class": "NFD-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_treaty(treaty, repo_root=self._repo_root)
        self._write_federation_overlay(treaty)
        self._emit_federation_adoption_ledger(session_id, treaty)
        return {"outcome": "adopted", "treaty": treaty, "nfd_class": "NFD-2"}

    def _write_federation_overlay(self, treaty: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._overlay_path.is_file():
                try:
                    payload = json.loads(self._overlay_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            treaties = list(payload.get("adopted_treaties") or [])
            treaties = [t for t in treaties if str(t.get("treaty_id")) != str(treaty.get("treaty_id"))]
            treaties.append(treaty)
            payload = {
                "norm_federation_overlay_version": "jarvis_memory_board_norm_federation.v1",
                "civilizational_tier": 16,
                "module_id": "capability_norm_federation_v1",
                "adopted_treaties": treaties,
                "updated_at": _utc_now_iso(),
            }
            self._overlay_path.parent.mkdir(parents=True, exist_ok=True)
            self._overlay_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def federation_posture(self) -> dict[str, Any]:
        return {
            "candidate_treaties": len(self.list_candidates(limit=200)),
            "adopted_treaties": len(adopted_treaties(repo_root=self._repo_root)),
            "claim_label": "asserted",
        }

    def federation_snapshot(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=20)
        drift_events: list[dict[str, Any]] = []
        try:
            from src.culture_of_beings_registry import adopted_norms

            norm_count = len(adopted_norms(repo_root=self._repo_root))
        except Exception:
            norm_count = 0
        if norm_count < 2 and not candidates:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="federation_posture",
                    summary="Insufficient adopted norms for treaty options; epistemic perimeter bounded to COB registry",
                )
            )
        payload = {
            "norm_federation_version": "operator_norm_federation.v1",
            "posture": self.federation_posture(),
            "adopted_treaties": adopted_treaties(repo_root=self._repo_root),
            "recent_candidates": candidates,
            "claim_label": "asserted",
        }
        return attach_charter_surfaces(
            payload,
            domain="norm_federation",
            declared_scopes=["cob_2_norms", "charter_refs", "membrane_envelope", "operator_ledger"],
            drift_events=drift_events,
            upstream_evidence_count=norm_count,
            candidates=candidates,
        )

    def _emit_federation_adoption_ledger(self, session_id: str, treaty: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_norm_federation_adoption_event

            append_norm_federation_adoption_event(session_id, treaty=treaty)
        except Exception:
            pass

    def _emit_federation_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_norm_federation_drift_event

            append_norm_federation_drift_event(session_id, drift=drift)
        except Exception:
            pass


norm_federation_runtime = NormFederationRuntime()
