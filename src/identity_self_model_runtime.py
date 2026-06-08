"""Identity self-model runtime — drift observation and governed adoption (Stage 6 / Release 37)."""

# Mythic: Identity Self-Model Runtime
# Engineering: IdentitySelfModelRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.identity_self_model_registry import CLAIM_VERSION, adopted_claims, save_adopted_claim
from src.super_nova_anchor import (
    SuperNovaIdentityAnchor,
    build_default_super_nova_identity_anchor,
)

DRIFT_VERSION = "identity_drift.v1"

FORBIDDEN_CLAIM_PHRASES = (
    "identity_mutation",
    "law_mutation",
    "authority_inflation",
    "override jarvis",
    "jarvis override",
    "repo mutation",
    "verification override",
    "cross_session_emotional",
    "hidden governance",
    "nova owns execution",
    "self-authorize",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_claim_against_anchor(
    claim: dict[str, Any],
    *,
    anchor: SuperNovaIdentityAnchor | None = None,
) -> dict[str, Any]:
    """Reject claims that violate immutable law or disallowed mutations."""
    active = anchor or build_default_super_nova_identity_anchor()
    statement = str(claim.get("statement") or "").lower()
    violations: list[str] = []
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase.replace("_", " ") in statement or phrase in statement:
            violations.append(f"forbidden_phrase:{phrase}")
    for mutation in active.disallowed_mutations:
        normalized = str(mutation).replace("_", " ")
        if normalized in statement:
            violations.append(f"disallowed_mutation:{mutation}")
    aligned = len(violations) == 0
    return {
        "aligned": aligned,
        "violations": violations,
        "anchor_authority_owner": active.authority_owner,
        "claim_label": "asserted" if aligned else "rejected",
    }


class IdentitySelfModelRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "identity_claim_candidates"
        self._foundation_path = self._runtime_dir / "jarvis_memory_board_foundation.v1.json"
        self._lock = threading.Lock()

    def observe_identity_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """ICC-0 observe-only drift from ledger, coherence, anchor, and habits."""
        drift_events: list[dict[str, Any]] = []
        anchor = build_default_super_nova_identity_anchor()
        constitutional_aligned = self._constitutional_bridge_aligned()

        if not constitutional_aligned:
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="constitutional_bridge",
                    summary="Constitutional bridge layer misaligned",
                    anchor_aligned=False,
                )
            )

        scopes = [str(session_id)] if session_id else ["global"]
        habit_adoptions = 0
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).isoformat()
            for scope in scopes:
                for row in operator_decision_ledger_store.list_events(scope, since=since, limit=500):
                    kind = str(row.get("decision_kind") or "")
                    if kind == "habit_adoption":
                        habit_adoptions += 1
                    if kind in {"brain_decision", "habit_adoption"} and row.get("decision") == "reject":
                        drift_events.append(
                            self._drift_event(
                                severity="nominal",
                                source=f"ledger:{kind}",
                                summary=str(row.get("summary") or "")[:120],
                                anchor_aligned=True,
                            )
                        )
        except Exception:
            pass

        candidates = self.surface_identity_candidates(session_id=session_id)
        ladder = self.candidates_from_stable_habits()
        for item in ladder:
            candidates.append(item)

        for candidate in candidates:
            self._persist_candidate(candidate)

        overall_aligned = constitutional_aligned and not any(
            d.get("severity") == "conflict" for d in drift_events
        )

        result = {
            "outcome": "observed",
            "icc_class": "ICC-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "anchor_aligned": overall_aligned,
            "anchor_authority_owner": anchor.authority_owner,
            "habit_adoptions_in_window": habit_adoptions,
            "window_days": window_days,
            "claim_label": "asserted",
            "summary": f"Identity drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_identity_drift_ledger(session_id, result)
        return result

    def _constitutional_bridge_aligned(self) -> bool:
        try:
            from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

            fabric = build_coherence_fabric_status()
            return bool(fabric.get("constitutional_bridge_aligned"))
        except Exception:
            return True

    def _drift_event(
        self,
        *,
        severity: str,
        source: str,
        summary: str,
        anchor_aligned: bool,
    ) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"drift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "anchor_aligned": anchor_aligned,
            "icc_class": "ICC-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_identity_candidates(self, *, session_id: str | None = None) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        anchor = build_default_super_nova_identity_anchor()
        for truth in anchor.immutable_identity[:3]:
            candidate = self._build_candidate(
                statement=f"Identity truth: {truth}",
                claim_kind="doctrine",
                evidence_refs=[f"anchor:immutable_identity:{truth[:32]}"],
                stability_score=1.0,
            )
            validation = validate_claim_against_anchor(candidate, anchor=anchor)
            if validation.get("aligned"):
                candidate["anchor_alignment"] = True
                candidates.append(candidate)
        for law in anchor.immutable_law[:2]:
            candidate = self._build_candidate(
                statement=f"Constitutional boundary: {law.replace('_', ' ')}",
                claim_kind="constitutional",
                evidence_refs=[f"anchor:immutable_law:{law}"],
                stability_score=1.0,
            )
            validation = validate_claim_against_anchor(candidate, anchor=anchor)
            if validation.get("aligned"):
                candidate["anchor_alignment"] = True
                candidates.append(candidate)
        return candidates

    def candidates_from_stable_habits(
        self,
        *,
        min_age_days: int = 14,
        min_occurrence: int = 5,
    ) -> list[dict[str, Any]]:
        """37c: stable HCC-2 habits → ICC-1 candidates only (never auto-adopt)."""
        try:
            from src.culture_habit_registry import adopted_habits as culture_adopted

            habits = culture_adopted(repo_root=self._repo_root)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, min_age_days))
        for habit in habits:
            if not habit.get("operator_promoted"):
                continue
            count = int(habit.get("occurrence_count") or 0)
            if count < min_occurrence:
                continue
            last_seen = str(habit.get("last_seen_at") or "")
            if last_seen:
                try:
                    seen = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                    if seen > cutoff:
                        continue
                except ValueError:
                    pass
            statement = (
                f"Stable routing habit: {habit.get('pattern_kind')} "
                f"{habit.get('source_family_id') or ''} -> {habit.get('target_family_id') or ''}"
            ).strip()
            candidate = self._build_candidate(
                statement=statement,
                claim_kind="boundary",
                evidence_refs=[f"habit:{habit.get('habit_id')}"],
                stability_score=float(count),
                icc_class="ICC-1",
                source_habit_id=habit.get("habit_id"),
            )
            validation = validate_claim_against_anchor(candidate)
            candidate["anchor_alignment"] = bool(validation.get("aligned"))
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def _build_candidate(
        self,
        *,
        statement: str,
        claim_kind: str,
        evidence_refs: list[str],
        stability_score: float,
        icc_class: str = "ICC-1",
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "claim_version": CLAIM_VERSION,
            "candidate_id": f"icand_{uuid4().hex[:12]}",
            "claim_kind": claim_kind,
            "statement": statement[:500],
            "evidence_refs": evidence_refs,
            "stability_score": stability_score,
            "anchor_alignment": False,
            "claim_label": "asserted",
            "operator_promoted": False,
            "icc_class": icc_class,
            **extra,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"icand_{uuid4().hex[:12]}")
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

    def rank_identity_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_identity_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()

        def score(item: dict[str, Any]) -> float:
            base = float(item.get("stability_score") or 0)
            if item.get("anchor_alignment"):
                base += 3.0
            stmt = str(item.get("statement") or "").lower()
            if lowered and any(word in stmt for word in lowered.split() if len(word) > 3):
                base += 2.0
            return base

        return sorted(candidates, key=score, reverse=True)[:8]

    def adopt_identity_claim(
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

        validation = validate_claim_against_anchor(candidate)
        if not validation.get("aligned"):
            return {
                "outcome": "blocked",
                "reason": "anchor_validation_failed",
                "violations": validation.get("violations"),
            }

        claim_id = f"claim_{uuid4().hex[:12]}"
        claim = {
            "claim_version": CLAIM_VERSION,
            "claim_id": claim_id,
            "claim_kind": str(candidate.get("claim_kind") or "doctrine"),
            "statement": str(candidate.get("statement") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "anchor_alignment": True,
            "stability_score": float(candidate.get("stability_score") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "icc_class": "ICC-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_claim(claim, repo_root=self._repo_root)
        self._write_foundation_slot(claim)
        self._emit_identity_adoption_ledger(session_id, claim)
        return {"outcome": "adopted", "claim": claim, "icc_class": "ICC-2"}

    def _write_foundation_slot(self, claim: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._foundation_path.is_file():
                try:
                    payload = json.loads(self._foundation_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            claims = list(payload.get("adopted_claims") or [])
            claims = [c for c in claims if str(c.get("claim_id")) != str(claim.get("claim_id"))]
            claims.append(claim)
            payload = {
                "foundation_overlay_version": "jarvis_memory_board_foundation.v1",
                "slot_id": "slot_01",
                "module_id": "capability_foundation_v2",
                "adopted_claims": claims,
                "updated_at": _utc_now_iso(),
            }
            self._foundation_path.parent.mkdir(parents=True, exist_ok=True)
            self._foundation_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def identity_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_claims(repo_root=self._repo_root)
        drift_count = len([c for c in candidates if not c.get("anchor_alignment")])
        return {
            "candidate_claims": len(candidates),
            "adopted_claims": len(adopted),
            "identity_drift_events": drift_count,
            "anchor_aligned": drift_count == 0,
            "claim_label": "asserted",
        }

    def identity_snapshot(self) -> dict[str, Any]:
        anchor = build_default_super_nova_identity_anchor()
        return {
            "identity_version": "operator_identity.v1",
            "posture": self.identity_posture(),
            "adopted_claims": adopted_claims(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "anchor": {
                "family_name": anchor.family_name,
                "authority_owner": anchor.authority_owner,
                "conflict_resolution_order": list(anchor.conflict_resolution_order),
            },
            "claim_label": "asserted",
        }

    def _emit_identity_adoption_ledger(self, session_id: str, claim: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_identity_adoption_event

            append_identity_adoption_event(session_id, claim=claim)
        except Exception:
            pass

    def _emit_identity_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_identity_drift_event

            append_identity_drift_event(session_id, drift=drift)
        except Exception:
            pass


identity_self_model_runtime = IdentitySelfModelRuntime()
