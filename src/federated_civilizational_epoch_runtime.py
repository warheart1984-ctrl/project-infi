"""Federated civilizational epoch runtime — Stage 19 / Release 49."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.federated_civilizational_epoch_registry import (
    CHARTER_VERSION,
    default_epoch_id,
    get_charter_template,
    is_epoch_amendable,
    load_adopted_charters,
    load_registry,
    save_adopted_charter,
    validate_witness_quorum,
)
from src.governed_civilization_registry import adopted_civilizations
from src.governed_civilization_runtime import validate_civilization_against_upstream_envelope

DRIFT_VERSION = "federated_epoch_drift.v1"


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _population_fixture_n() -> int:
    raw = os.getenv("AAIS_POPULATION_FIXTURE_N", "0")
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def validate_federated_epoch_against_upstream(
    charter: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    violations: list[str] = []
    epoch_id = str(charter.get("epoch_id") or default_epoch_id(repo_root=repo_root))
    epoch_check = is_epoch_amendable(epoch_id, repo_root=repo_root)
    if not epoch_check.get("amendable"):
        violations.extend(list(epoch_check.get("violations") or []))
    upstream = list(charter.get("upstream_refs") or ["GCV", "ISD", "NFD", "CEV"])
    if "GCV" in upstream:
        civilizations = adopted_civilizations(repo_root=repo_root)
        if not civilizations:
            violations.append("gcv_upstream_not_satisfied")
        else:
            probe = {
                "summary": str(charter.get("summary") or ""),
                "admitted_charter_ids": list(civilizations[0].get("admitted_charter_ids") or ["a", "b"]),
            }
            gcv = validate_civilization_against_upstream_envelope(probe, repo_root=repo_root)
            if not gcv.get("aligned"):
                violations.extend([f"gcv:{v}" for v in gcv.get("violations") or []])
    lowered = str(charter.get("summary") or "").lower()
    if "autonomous rewrite" in lowered or "self-rewrite" in lowered:
        violations.append("forbidden_autonomous_rewrite_language")
    aligned = len(violations) == 0
    return {"aligned": aligned, "violations": violations, "claim_label": "asserted" if aligned else "rejected"}


class FederatedCivilizationalEpochRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "federated_epoch_charter_candidates"
        self._overlay_path = self._runtime_dir / "jarvis_memory_board_federated_epoch.v1.json"
        self._lock = threading.Lock()

    def observe_epoch_drift(self, *, session_id: str | None = None, window_days: int = 30) -> dict[str, Any]:
        drift_events: list[dict[str, Any]] = []
        adopted = load_adopted_charters(runtime_dir=self._runtime_dir)
        reg = load_registry(repo_root=self._repo_root)
        epoch_id = default_epoch_id(repo_root=self._repo_root)
        epoch = is_epoch_amendable(epoch_id, repo_root=self._repo_root)
        if not epoch.get("amendable"):
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="epoch_window",
                    summary=f"Default epoch not amendable: {epoch.get('reason')}",
                )
            )
        population_n = _population_fixture_n()
        candidates = self.surface_epoch_candidates()
        for candidate in candidates:
            self._persist_candidate(candidate)
        result = {
            "outcome": "observed",
            "fce_class": "FCE-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "adopted_charter_count": len(adopted),
            "epoch_id": epoch_id,
            "epoch_amendable": epoch.get("amendable"),
            "population_member_count": population_n,
            "charter_cardinality": len(adopted),
            "operator_quorum_hint": max(1, len(reg.get("charter_templates") or [])),
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": (
                f"Federated epoch drift observed: {len(drift_events)} events, "
                f"{len(candidates)} candidates, population_fixture={population_n}"
            ),
        }
        if session_id:
            self._emit_epoch_drift_ledger(session_id, result)
        return result

    def _drift_event(self, *, severity: str, source: str, summary: str) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"fcedrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "fce_class": "FCE-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_epoch_candidates(self) -> list[dict[str, Any]]:
        template = get_charter_template("fce_live_federation_v1", repo_root=self._repo_root)
        if not template:
            return []
        epoch_id = default_epoch_id(repo_root=self._repo_root)
        candidate = self._build_candidate(
            summary=str(template.get("summary") or "Live federated epoch charter"),
            epoch_id=epoch_id,
            template_id=str(template.get("template_id") or "fce_live_federation_v1"),
            upstream_refs=list(template.get("required_upstream") or []),
            coordination_class=str(template.get("coordination_class") or "FCE-1"),
            stability_score=0.9,
        )
        if validate_federated_epoch_against_upstream(candidate, repo_root=self._repo_root).get("aligned"):
            return [candidate]
        return []

    def _build_candidate(self, **fields: Any) -> dict[str, Any]:
        return {
            "charter_version": CHARTER_VERSION,
            "candidate_id": f"fcecand_{uuid4().hex[:12]}",
            "evidence_refs": [],
            "claim_label": "asserted",
            "operator_promoted": False,
            "fce_class": "FCE-1",
            **fields,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"fcecand_{uuid4().hex[:12]}")
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

    def list_epochs(self) -> list[dict[str, Any]]:
        from src.federated_civilizational_epoch_registry import list_epochs as registry_epochs

        return registry_epochs(repo_root=self._repo_root)

    def list_witnesses(self) -> list[dict[str, Any]]:
        witnesses: list[dict[str, Any]] = []
        for charter in load_adopted_charters(runtime_dir=self._runtime_dir):
            for witness in list(charter.get("external_witnesses") or []):
                row = dict(witness)
                row["charter_id"] = charter.get("charter_id")
                witnesses.append(row)
        return witnesses

    def adopt_federated_epoch_charter(
        self,
        candidate: dict[str, Any],
        *,
        operator_approved: bool = False,
        jarvis_authorization: dict[str, Any] | None = None,
        external_witnesses: list[dict[str, Any]] | None = None,
        operator_org_domain: str | None = None,
        session_id: str = "global",
    ) -> dict[str, Any]:
        if not operator_approved:
            return {"outcome": "blocked", "reason": "operator_approved required", "status": 403}
        auth = dict(jarvis_authorization or {})
        if not auth.get("authorized"):
            return {"outcome": "blocked", "reason": "jarvis_not_authorized", "status": 403}
        template_id = str(candidate.get("template_id") or "fce_live_federation_v1")
        template = get_charter_template(template_id, repo_root=self._repo_root) or {}
        min_witnesses = int(template.get("min_external_witnesses") or 1)
        witnesses = list(external_witnesses or candidate.get("external_witnesses") or [])
        witness_check = validate_witness_quorum(
            witnesses,
            operator_org_domain=operator_org_domain or os.getenv("AAIS_OPERATOR_ORG_DOMAIN"),
            min_external=min_witnesses,
        )
        if not witness_check.get("aligned"):
            return {
                "outcome": "blocked",
                "reason": "witness_quorum_failed",
                "violations": witness_check.get("violations"),
            }
        validation = validate_federated_epoch_against_upstream(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {
                "outcome": "blocked",
                "reason": "alignment_validation_failed",
                "violations": validation.get("violations"),
            }
        charter_id = f"fce_{uuid4().hex[:12]}"
        population_n = _population_fixture_n()
        charter = {
            "charter_version": CHARTER_VERSION,
            "charter_id": charter_id,
            "epoch_id": str(candidate.get("epoch_id") or default_epoch_id(repo_root=self._repo_root)),
            "template_id": template_id,
            "upstream_refs": list(candidate.get("upstream_refs") or []),
            "external_witnesses": witnesses,
            "summary": str(candidate.get("summary") or "")[:500],
            "stability_score": float(candidate.get("stability_score") or 0),
            "population_member_count": population_n or int(candidate.get("population_member_count") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "fce_class": "FCE-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_charter(charter, runtime_dir=self._runtime_dir)
        self._write_epoch_overlay(charter)
        self._emit_epoch_adoption_ledger(session_id, charter)
        return {"outcome": "adopted", "charter": charter, "fce_class": "FCE-2"}

    def _write_epoch_overlay(self, charter: dict[str, Any]) -> None:
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
                "federated_epoch_overlay_version": "jarvis_memory_board_federated_epoch.v1",
                "civilizational_tier": 19,
                "module_id": "capability_federated_civilizational_epoch_v1",
                "adopted_charters": charters,
                "updated_at": _utc_now_iso(),
            }
            self._overlay_path.parent.mkdir(parents=True, exist_ok=True)
            self._overlay_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def epoch_posture(self) -> dict[str, Any]:
        return {
            "candidate_charters": len(self.list_candidates(limit=200)),
            "adopted_charters": len(load_adopted_charters(runtime_dir=self._runtime_dir)),
            "population_fixture_n": _population_fixture_n(),
            "claim_label": "asserted",
        }

    def epoch_snapshot(self) -> dict[str, Any]:
        return {
            "federated_epoch_version": CHARTER_VERSION,
            "posture": self.epoch_posture(),
            "adopted_charters": load_adopted_charters(runtime_dir=self._runtime_dir),
            "epochs": self.list_epochs(),
            "recent_candidates": self.list_candidates(limit=20),
            "claim_label": "asserted",
        }

    def _emit_epoch_adoption_ledger(self, session_id: str, charter: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_federated_epoch_adoption_event

            append_federated_epoch_adoption_event(session_id, charter=charter)
        except Exception:
            pass

    def _emit_epoch_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_federated_epoch_drift_event

            append_federated_epoch_drift_event(session_id, drift=drift)
        except Exception:
            pass


federated_civilizational_epoch_runtime = FederatedCivilizationalEpochRuntime()
