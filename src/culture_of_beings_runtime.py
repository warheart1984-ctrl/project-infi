"""Culture-of-beings runtime — cross-organism norm drift fusion and governed adoption (Stage 11 / Release 42)."""

# Mythic: Culture-of-Beings Runtime
# Engineering: CultureOfBeingsRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.culture_of_beings_registry import NORM_VERSION, adopted_norms, save_adopted_norm
from src.multi_being_continuity_registry import adopted_pacts
from src.multi_being_continuity_runtime import validate_pact_against_identity_narrative_agency_and_social

DRIFT_VERSION = "culture_of_beings_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_norm_against_identity_narrative_agency_social_and_pacts(
    norm: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Reject norms that violate upstream layers or contradict adopted MBC-2 pacts."""
    as_pact = {
        "summary": str(norm.get("summary") or ""),
        "pact_kind": "bilateral_organism",
    }
    pact_check = validate_pact_against_identity_narrative_agency_and_social(as_pact, repo_root=repo_root)
    violations = list(pact_check.get("violations") or [])
    pact_aligned = True
    lowered = str(norm.get("summary") or "").lower()
    try:
        pacts = adopted_pacts(repo_root=repo_root)
        if pacts and any("override jarvis" in lowered or "bypass membrane" in lowered):
            pact_aligned = False
            violations.append("contradicts_pact_posture")
    except Exception:
        pass
    aligned = pact_check.get("aligned") and pact_aligned and len(violations) == 0
    return {
        "aligned": aligned,
        "identity_alignment": bool(pact_check.get("identity_alignment")),
        "narrative_alignment": bool(pact_check.get("narrative_alignment")),
        "agency_alignment": bool(pact_check.get("agency_alignment")),
        "social_alignment": bool(pact_check.get("social_alignment")),
        "pact_alignment": pact_aligned,
        "violations": violations,
        "claim_label": "asserted" if aligned else "rejected",
    }


class CultureOfBeingsRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "shared_norm_candidates"
        self._overlay_path = self._runtime_dir / "jarvis_memory_board_culture_of_beings.v1.json"
        self._lock = threading.Lock()

    def observe_culture_of_beings_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """COB-0 observe-only drift from MBC posture, mesh, exchange, and ledger signals."""
        drift_events: list[dict[str, Any]] = []
        mbc_posture = self._mbc_posture_safe()

        if not mbc_posture.get("identity_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="multi_being_posture",
                    summary="Multi-being posture misaligned with identity",
                    identity_aligned=False,
                )
            )

        candidates = self.surface_norm_candidates()
        for ladder_fn in (
            self.candidates_from_adopted_pacts,
            self.candidates_from_mesh_clusters,
            self.candidates_from_exchange_patterns,
            self.candidates_from_arbitration_resolutions,
        ):
            for item in ladder_fn():
                candidates.append(item)

        for candidate in candidates:
            self._persist_candidate(candidate)

        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).isoformat()
            scope = str(session_id) if session_id else "global"
            for row in operator_decision_ledger_store.list_events(scope, since=since, limit=500):
                kind = str(row.get("decision_kind") or "")
                if kind in {"culture_of_beings_drift", "multi_being_arbitration", "multi_being_adoption"}:
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
            "cob_class": "COB-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "identity_aligned": mbc_posture.get("identity_aligned", True),
            "pact_aligned": mbc_posture.get("social_aligned", True),
            "adopted_pact_count": mbc_posture.get("adopted_pacts", 0),
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": f"Culture-of-beings drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_culture_of_beings_drift_ledger(session_id, result)
        return result

    def _mbc_posture_safe(self) -> dict[str, Any]:
        try:
            from src.multi_being_continuity_runtime import multi_being_continuity_runtime

            return multi_being_continuity_runtime.multi_being_posture()
        except Exception:
            return {"identity_aligned": True, "social_aligned": True, "adopted_pacts": 0}

    def _drift_event(
        self,
        *,
        severity: str,
        source: str,
        summary: str,
        identity_aligned: bool = True,
        pact_aligned: bool = True,
    ) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"cdrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "identity_aligned": identity_aligned,
            "pact_aligned": pact_aligned,
            "cob_class": "COB-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_norm_candidates(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        try:
            pacts = adopted_pacts(repo_root=self._repo_root)
        except Exception:
            pacts = []
        if pacts:
            pact = pacts[0]
            candidate = self._build_candidate(
                summary=f"Shared handoff norm from pact {pact.get('pact_id', '')[:12]}",
                norm_kind="handoff_ritual",
                cluster_ref=dict(pact.get("counterparty_organism_ref") or {}),
                continuity_posture="pact_grounded",
                trust_tier="governed_cluster",
                evidence_refs=[f"pact:{pact.get('pact_id')}"],
                stability_score=0.7,
                cob_class="COB-1",
            )
            validation = validate_norm_against_identity_narrative_agency_social_and_pacts(
                candidate, repo_root=self._repo_root
            )
            if validation.get("aligned"):
                candidate.update(validation)
                candidates.append(candidate)
        return candidates

    def candidates_from_adopted_pacts(self) -> list[dict[str, Any]]:
        try:
            pacts = adopted_pacts(repo_root=self._repo_root)
        except Exception:
            return []
        candidates: list[dict[str, Any]] = []
        for pact in pacts:
            if not pact.get("operator_promoted"):
                continue
            kind = str(pact.get("pact_kind") or "")
            norm_kind = "mesh_cluster" if kind == "federated_mesh_cluster" else "consent_cadence"
            candidate = self._build_candidate(
                summary=f"Shared norm from pact: {pact.get('summary', '')[:300]}",
                norm_kind=norm_kind,
                cluster_ref=dict(pact.get("counterparty_organism_ref") or {}),
                continuity_posture="pact_derived",
                trust_tier=str(pact.get("trust_tier") or "federation_verified"),
                evidence_refs=[f"pact:{pact.get('pact_id')}"],
                stability_score=float(pact.get("stability_score") or 0.8),
                cob_class="COB-1",
                source_layers={"pact_id": pact.get("pact_id")},
            )
            validation = validate_norm_against_identity_narrative_agency_social_and_pacts(
                candidate, repo_root=self._repo_root
            )
            candidate.update({k: validation.get(k) for k in validation if k.endswith("_alignment") or k == "aligned"})
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_mesh_clusters(self) -> list[dict[str, Any]]:
        cluster_counts: Counter[str] = Counter()
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            for row in operator_decision_ledger_store.list_events("global", since=since, limit=500):
                if str(row.get("decision_kind") or "") != "organ_mesh_run":
                    continue
                fed = dict(row.get("federation") or {})
                if fed.get("grant_id"):
                    cluster_counts[str(fed.get("grant_id"))] += 1
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for grant_id, count in cluster_counts.most_common(4):
            if count < 2:
                continue
            candidate = self._build_candidate(
                summary=f"Mesh cluster norm: {grant_id} ({count} cross-tenant runs)",
                norm_kind="mesh_cluster",
                cluster_ref={"grant_id": grant_id},
                continuity_posture="mesh_repeated",
                trust_tier="mesh_verified",
                evidence_refs=[f"mesh:{grant_id}"],
                stability_score=min(float(count) / 10.0, 1.0),
                cob_class="COB-1",
                source_layers={"grant_id": grant_id, "mesh_run_count": count},
            )
            validation = validate_norm_against_identity_narrative_agency_social_and_pacts(
                candidate, repo_root=self._repo_root
            )
            if validation.get("aligned"):
                candidate.update({k: validation.get(k) for k in validation if k.endswith("_alignment")})
                candidates.append(candidate)
        return candidates

    def candidates_from_exchange_patterns(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            exchange_count = 0
            for row in operator_decision_ledger_store.list_events("global", since=since, limit=300):
                if row.get("federation") and str(row.get("decision_kind") or "").endswith("_adoption"):
                    exchange_count += 1
            if exchange_count >= 1:
                candidate = self._build_candidate(
                    summary=f"Exchange protocol norm from {exchange_count} federated adoption(s)",
                    norm_kind="exchange_protocol",
                    cluster_ref={"scope": "federated"},
                    continuity_posture="exchange_observed",
                    trust_tier="consent_governed",
                    evidence_refs=["imxp:pattern"],
                    stability_score=min(exchange_count / 5.0, 1.0),
                    cob_class="COB-1",
                )
                validation = validate_norm_against_identity_narrative_agency_social_and_pacts(
                    candidate, repo_root=self._repo_root
                )
                if validation.get("aligned"):
                    candidate.update({k: validation.get(k) for k in validation if k.endswith("_alignment")})
                    candidates.append(candidate)
        except Exception:
            pass
        return candidates

    def candidates_from_arbitration_resolutions(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            for row in operator_decision_ledger_store.list_events("global", since=since, limit=200):
                if str(row.get("decision_kind") or "") != "multi_being_arbitration":
                    continue
                conflict = dict(row.get("multi_being_arbitration") or {})
                candidate = self._build_candidate(
                    summary=f"Dispute posture norm: {conflict.get('summary', 'arbitration resolved')[:200]}",
                    norm_kind="dispute_posture",
                    cluster_ref={"arbitration_id": row.get("decision_id")},
                    continuity_posture="arbitration_grounded",
                    trust_tier="governed_dispute",
                    evidence_refs=[f"arbitration:{row.get('decision_id', 'unknown')}"],
                    stability_score=0.85,
                    cob_class="COB-1",
                )
                validation = validate_norm_against_identity_narrative_agency_social_and_pacts(
                    candidate, repo_root=self._repo_root
                )
                if validation.get("aligned"):
                    candidate.update({k: validation.get(k) for k in validation if k.endswith("_alignment")})
                    candidates.append(candidate)
        except Exception:
            pass
        return candidates[:4]

    def _build_candidate(
        self,
        *,
        summary: str,
        norm_kind: str,
        cluster_ref: dict[str, Any],
        continuity_posture: str,
        trust_tier: str,
        evidence_refs: list[str],
        stability_score: float,
        cob_class: str = "COB-1",
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "norm_version": NORM_VERSION,
            "candidate_id": f"ncand_{uuid4().hex[:12]}",
            "norm_kind": norm_kind,
            "cluster_ref": cluster_ref,
            "continuity_posture": continuity_posture,
            "trust_tier": trust_tier,
            "summary": summary[:500],
            "evidence_refs": evidence_refs,
            "stability_score": stability_score,
            "identity_alignment": False,
            "narrative_alignment": False,
            "agency_alignment": False,
            "social_alignment": False,
            "pact_alignment": False,
            "claim_label": "asserted",
            "operator_promoted": False,
            "cob_class": cob_class,
            **extra,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"ncand_{uuid4().hex[:12]}")
        candidate["candidate_id"] = cid
        with self._lock:
            self._candidates_dir.mkdir(parents=True, exist_ok=True)
            path = self._candidates_dir / f"{cid}.json"
            path.write_text(json.dumps(candidate, sort_keys=True) + "\n", encoding="utf-8")

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

    def rank_shared_norm_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_culture_of_beings_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()

        def score(item: dict[str, Any]) -> float:
            base = float(item.get("stability_score") or 0)
            for flag in ("identity_alignment", "narrative_alignment", "agency_alignment", "social_alignment", "pact_alignment"):
                if item.get(flag):
                    base += 2.0
            stmt = str(item.get("summary") or "").lower()
            if lowered and any(word in stmt for word in lowered.split() if len(word) > 3):
                base += 2.0
            return base

        return sorted(candidates, key=score, reverse=True)[:8]

    def adopt_shared_norm(
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
        if not candidate:
            return {"outcome": "blocked", "reason": "empty_candidate"}

        validation = validate_norm_against_identity_narrative_agency_social_and_pacts(
            candidate, repo_root=self._repo_root
        )
        if not validation.get("aligned"):
            return {
                "outcome": "blocked",
                "reason": "alignment_validation_failed",
                "violations": validation.get("violations"),
            }

        norm_id = f"norm_{uuid4().hex[:12]}"
        norm = {
            "norm_version": NORM_VERSION,
            "norm_id": norm_id,
            "norm_kind": str(candidate.get("norm_kind") or "handoff_ritual"),
            "cluster_ref": dict(candidate.get("cluster_ref") or {}),
            "continuity_posture": str(candidate.get("continuity_posture") or "governed"),
            "trust_tier": str(candidate.get("trust_tier") or "governed_cluster"),
            "summary": str(candidate.get("summary") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "source_layers": dict(candidate.get("source_layers") or {}),
            "identity_alignment": True,
            "narrative_alignment": True,
            "agency_alignment": True,
            "social_alignment": True,
            "pact_alignment": True,
            "stability_score": float(candidate.get("stability_score") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "cob_class": "COB-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_norm(norm, repo_root=self._repo_root)
        self._write_culture_of_beings_slot(norm)
        self._emit_culture_of_beings_adoption_ledger(session_id, norm)
        return {"outcome": "adopted", "norm": norm, "cob_class": "COB-2"}

    def _write_culture_of_beings_slot(self, norm: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._overlay_path.is_file():
                try:
                    payload = json.loads(self._overlay_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            norms = list(payload.get("adopted_norms") or [])
            norms = [n for n in norms if str(n.get("norm_id")) != str(norm.get("norm_id"))]
            norms.append(norm)
            payload = {
                "culture_of_beings_overlay_version": "jarvis_memory_board_culture_of_beings.v1",
                "slot_id": "slot_09",
                "module_id": "capability_culture_of_beings_v1",
                "adopted_norms": norms,
                "updated_at": _utc_now_iso(),
            }
            self._overlay_path.parent.mkdir(parents=True, exist_ok=True)
            self._overlay_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def culture_of_beings_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_norms(repo_root=self._repo_root)
        drift_count = len([c for c in candidates if not c.get("identity_alignment")])
        return {
            "candidate_norms": len(candidates),
            "adopted_norms": len(adopted),
            "culture_of_beings_drift_events": drift_count,
            "identity_aligned": drift_count == 0,
            "pact_aligned": drift_count == 0,
            "cluster_norm_count": len([n for n in adopted if n.get("norm_kind") == "mesh_cluster"]),
            "claim_label": "asserted",
        }

    def culture_of_beings_snapshot(self) -> dict[str, Any]:
        return {
            "culture_of_beings_version": "operator_culture_of_beings.v1",
            "posture": self.culture_of_beings_posture(),
            "adopted_norms": adopted_norms(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "claim_label": "asserted",
        }

    def _emit_culture_of_beings_adoption_ledger(self, session_id: str, norm: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_culture_of_beings_adoption_event

            append_culture_of_beings_adoption_event(session_id, norm=norm)
        except Exception:
            pass

    def _emit_culture_of_beings_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_culture_of_beings_drift_event

            append_culture_of_beings_drift_event(session_id, drift=drift)
        except Exception:
            pass


culture_of_beings_runtime = CultureOfBeingsRuntime()
