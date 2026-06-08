"""Narrative continuity runtime — life-story drift fusion and governed adoption (Stage 7 / Release 38)."""

# Mythic: Narrative Continuity Runtime
# Engineering: NarrativeContinuityRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.cog_runtime.narrative_continuity import score_continuity_completeness
from src.cog_runtime.narrative_store import load_narrative_store, resolve_narrative_store_root
from src.identity_self_model_runtime import validate_claim_against_anchor
from src.narrative_continuity_registry import BEAT_VERSION, adopted_beats, save_adopted_beat

DRIFT_VERSION = "narrative_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_beat_against_identity(
    beat: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Reject beats that violate anchor law or contradict adopted identity claims."""
    summary = str(beat.get("summary") or "")
    as_claim = {"statement": summary, "claim_kind": "doctrine"}
    anchor_check = validate_claim_against_anchor(as_claim)
    violations = list(anchor_check.get("violations") or [])
    try:
        from src.identity_self_model_registry import adopted_claims as identity_adopted

        for claim in identity_adopted(repo_root=repo_root):
            claim_stmt = str(claim.get("statement") or "").lower()
            if not claim_stmt:
                continue
            if "boundary" in str(claim.get("claim_kind") or "") and "override" in summary.lower():
                if "jarvis" in claim_stmt or "authority" in claim_stmt:
                    violations.append(f"contradicts_identity:{claim.get('claim_id')}")
    except Exception:
        pass
    aligned = len(violations) == 0
    return {
        "aligned": aligned,
        "violations": violations,
        "claim_label": "asserted" if aligned else "rejected",
    }


class NarrativeContinuityRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "narrative_beat_candidates"
        self._session_path = self._runtime_dir / "jarvis_memory_board_session.v1.json"
        self._lock = threading.Lock()

    def observe_narrative_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """NCC-0 observe-only drift from ledger, identity, habits, mesh, Nova store."""
        drift_events: list[dict[str, Any]] = []
        identity_posture = self._identity_posture_safe()
        if not identity_posture.get("anchor_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="identity_posture",
                    summary="Identity posture misaligned with anchor",
                    identity_aligned=False,
                )
            )

        nova_snapshot = self._load_nova_snapshot()
        completeness = score_continuity_completeness(nova_snapshot.get("narrative"))
        if not completeness.get("complete"):
            drift_events.append(
                self._drift_event(
                    severity="nominal",
                    source="nova_narrative",
                    summary="Nova continuity questions incomplete",
                    identity_aligned=True,
                )
            )

        scopes = [str(session_id)] if session_id else ["global"]
        mesh_runs = 0
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).isoformat()
            for scope in scopes:
                for row in operator_decision_ledger_store.list_events(scope, since=since, limit=500):
                    kind = str(row.get("decision_kind") or "")
                    if kind == "organ_mesh_run":
                        mesh_runs += 1
                    if kind in {"identity_drift", "narrative_drift"}:
                        drift_events.append(
                            self._drift_event(
                                severity="nominal",
                                source=f"ledger:{kind}",
                                summary=str(row.get("summary") or "")[:120],
                                identity_aligned=True,
                            )
                        )
        except Exception:
            pass

        candidates = self.surface_narrative_candidates()
        for ladder_fn in (
            self.candidates_from_adopted_identity,
            self.candidates_from_stable_habits,
            self.candidates_from_nova_store,
        ):
            for item in ladder_fn():
                candidates.append(item)

        for candidate in candidates:
            self._persist_candidate(candidate)

        continuity_score = float(completeness.get("score") or 0.0)
        overall_aligned = identity_posture.get("anchor_aligned", True) and not any(
            d.get("severity") == "conflict" for d in drift_events
        )

        result = {
            "outcome": "observed",
            "ncc_class": "NCC-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "identity_aligned": overall_aligned,
            "continuity_score": continuity_score,
            "mesh_runs_in_window": mesh_runs,
            "window_days": window_days,
            "nova_summary": {
                "active_story": nova_snapshot.get("narrative", {}).get("active_story"),
                "open_thread_count": len(nova_snapshot.get("narrative", {}).get("open_threads") or []),
            },
            "claim_label": "asserted",
            "summary": f"Narrative drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_narrative_drift_ledger(session_id, result)
        return result

    def _identity_posture_safe(self) -> dict[str, Any]:
        try:
            from src.identity_self_model_runtime import identity_self_model_runtime

            return identity_self_model_runtime.identity_posture()
        except Exception:
            return {"anchor_aligned": True}

    def _load_nova_snapshot(self) -> dict[str, Any]:
        try:
            store_root = resolve_narrative_store_root(
                self._runtime_dir / "nova_narrative" if self._runtime_dir else None
            )
            record = load_narrative_store("default", store_root=store_root)
            if record:
                return {"narrative": dict(record.get("narrative") or {}), "narrative_id": "default"}
        except Exception:
            pass
        return {"narrative": {}, "narrative_id": "default"}

    def _drift_event(
        self,
        *,
        severity: str,
        source: str,
        summary: str,
        identity_aligned: bool,
    ) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"ndrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "identity_aligned": identity_aligned,
            "ncc_class": "NCC-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_narrative_candidates(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        nova = self._load_nova_snapshot().get("narrative") or {}
        chapter = str(nova.get("current_chapter") or "").strip()
        if chapter:
            candidate = self._build_candidate(
                summary=f"Current chapter: {chapter}",
                beat_kind="chapter",
                evidence_refs=[f"nova:current_chapter:{chapter[:32]}"],
                stability_score=0.8,
            )
            if validate_beat_against_identity(candidate, repo_root=self._repo_root).get("aligned"):
                candidate["identity_alignment"] = True
                candidates.append(candidate)
        for thread in list(nova.get("open_threads") or [])[:5]:
            text = str(thread).strip()
            if not text:
                continue
            candidate = self._build_candidate(
                summary=f"Open thread: {text}",
                beat_kind="thread",
                evidence_refs=[f"nova:open_thread:{text[:32]}"],
                stability_score=0.6,
            )
            validation = validate_beat_against_identity(candidate, repo_root=self._repo_root)
            if validation.get("aligned"):
                candidate["identity_alignment"] = True
                candidates.append(candidate)
        return candidates

    def candidates_from_adopted_identity(self, *, min_age_days: int = 14) -> list[dict[str, Any]]:
        """38c: ICC-2 claims → NCC-1 chapter candidates only."""
        try:
            from src.identity_self_model_registry import adopted_claims as identity_adopted

            claims = identity_adopted(repo_root=self._repo_root)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for claim in claims:
            if not claim.get("operator_promoted"):
                continue
            kind = str(claim.get("claim_kind") or "")
            if kind not in {"doctrine", "boundary", "constitutional"}:
                continue
            statement = str(claim.get("statement") or "")[:400]
            candidate = self._build_candidate(
                summary=f"Identity chapter: {statement}",
                beat_kind="chapter",
                evidence_refs=[f"identity:{claim.get('claim_id')}"],
                stability_score=float(claim.get("stability_score") or 1.0),
                ncc_class="NCC-1",
                source_layers={"identity_claim_id": claim.get("claim_id")},
            )
            validation = validate_beat_against_identity(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = bool(validation.get("aligned"))
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_stable_habits(
        self,
        *,
        min_age_days: int = 14,
        min_occurrence: int = 5,
    ) -> list[dict[str, Any]]:
        """38c: HCC-2 habits → NCC-1 thread candidates only."""
        try:
            from src.culture_habit_registry import adopted_habits as culture_adopted

            habits = culture_adopted(repo_root=self._repo_root)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for habit in habits:
            if not habit.get("operator_promoted"):
                continue
            count = int(habit.get("occurrence_count") or 0)
            if count < min_occurrence:
                continue
            summary = (
                f"Recurring mesh thread: {habit.get('source_family_id')} -> "
                f"{habit.get('target_family_id')} ({habit.get('pattern_kind')})"
            )
            candidate = self._build_candidate(
                summary=summary,
                beat_kind="thread",
                evidence_refs=[f"habit:{habit.get('habit_id')}"],
                stability_score=float(count),
                ncc_class="NCC-1",
                source_layers={"habit_id": habit.get("habit_id")},
            )
            validation = validate_beat_against_identity(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = bool(validation.get("aligned"))
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_nova_store(self) -> list[dict[str, Any]]:
        """Nova open_threads / promises → NCC-1 candidates (read-only ingest)."""
        nova = self._load_nova_snapshot().get("narrative") or {}
        candidates: list[dict[str, Any]] = []
        for promise in list(nova.get("promises") or [])[:5]:
            if not isinstance(promise, dict):
                continue
            text = str(promise.get("promise") or "").strip()
            if not text:
                continue
            candidate = self._build_candidate(
                summary=f"Promise closure candidate: {text}",
                beat_kind="promise_closure",
                evidence_refs=[f"nova:promise:{text[:32]}"],
                stability_score=0.7,
                ncc_class="NCC-1",
                source_layers={"narrative_id": "default"},
            )
            validation = validate_beat_against_identity(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = bool(validation.get("aligned"))
            if validation.get("aligned"):
                candidates.append(candidate)
        story = str(nova.get("active_story") or "").strip()
        if story:
            candidate = self._build_candidate(
                summary=f"Active arc: {story}",
                beat_kind="arc",
                evidence_refs=[f"nova:active_story:{story[:32]}"],
                stability_score=0.9,
                ncc_class="NCC-1",
                source_layers={"narrative_id": "default"},
            )
            validation = validate_beat_against_identity(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = bool(validation.get("aligned"))
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def _build_candidate(
        self,
        *,
        summary: str,
        beat_kind: str,
        evidence_refs: list[str],
        stability_score: float,
        ncc_class: str = "NCC-1",
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "beat_version": BEAT_VERSION,
            "candidate_id": f"ncand_{uuid4().hex[:12]}",
            "beat_kind": beat_kind,
            "summary": summary[:500],
            "evidence_refs": evidence_refs,
            "stability_score": stability_score,
            "identity_alignment": False,
            "claim_label": "asserted",
            "operator_promoted": False,
            "ncc_class": ncc_class,
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

    def rank_narrative_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_narrative_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()

        def score(item: dict[str, Any]) -> float:
            base = float(item.get("stability_score") or 0)
            if item.get("identity_alignment"):
                base += 3.0
            stmt = str(item.get("summary") or "").lower()
            if lowered and any(word in stmt for word in lowered.split() if len(word) > 3):
                base += 2.0
            return base

        return sorted(candidates, key=score, reverse=True)[:8]

    def adopt_narrative_beat(
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

        validation = validate_beat_against_identity(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {
                "outcome": "blocked",
                "reason": "identity_validation_failed",
                "violations": validation.get("violations"),
            }

        beat_id = f"beat_{uuid4().hex[:12]}"
        beat = {
            "beat_version": BEAT_VERSION,
            "beat_id": beat_id,
            "beat_kind": str(candidate.get("beat_kind") or "thread"),
            "summary": str(candidate.get("summary") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "source_layers": dict(candidate.get("source_layers") or {}),
            "identity_alignment": True,
            "stability_score": float(candidate.get("stability_score") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "ncc_class": "NCC-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_beat(beat, repo_root=self._repo_root)
        self._write_session_slot(beat)
        self._emit_narrative_adoption_ledger(session_id, beat)
        return {"outcome": "adopted", "beat": beat, "ncc_class": "NCC-2"}

    def _write_session_slot(self, beat: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._session_path.is_file():
                try:
                    payload = json.loads(self._session_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            beats = list(payload.get("adopted_beats") or [])
            beats = [b for b in beats if str(b.get("beat_id")) != str(beat.get("beat_id"))]
            beats.append(beat)
            payload = {
                "session_overlay_version": "jarvis_memory_board_session.v1",
                "slot_id": "slot_03",
                "module_id": "capability_session_v2",
                "adopted_beats": beats,
                "updated_at": _utc_now_iso(),
            }
            self._session_path.parent.mkdir(parents=True, exist_ok=True)
            self._session_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def narrative_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_beats(repo_root=self._repo_root)
        drift_count = len([c for c in candidates if not c.get("identity_alignment")])
        nova = self._load_nova_snapshot().get("narrative") or {}
        completeness = score_continuity_completeness(nova)
        return {
            "candidate_beats": len(candidates),
            "adopted_beats": len(adopted),
            "narrative_drift_events": drift_count,
            "identity_aligned": drift_count == 0,
            "continuity_score": float(completeness.get("score") or 0.0),
            "claim_label": "asserted",
        }

    def narrative_snapshot(self) -> dict[str, Any]:
        nova = self._load_nova_snapshot()
        return {
            "narrative_version": "operator_narrative.v1",
            "posture": self.narrative_posture(),
            "adopted_beats": adopted_beats(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "nova_summary": {
                "active_story": (nova.get("narrative") or {}).get("active_story"),
                "current_chapter": (nova.get("narrative") or {}).get("current_chapter"),
                "open_threads": list((nova.get("narrative") or {}).get("open_threads") or [])[:8],
            },
            "claim_label": "asserted",
        }

    def _emit_narrative_adoption_ledger(self, session_id: str, beat: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_narrative_adoption_event

            append_narrative_adoption_event(session_id, beat=beat)
        except Exception:
            pass

    def _emit_narrative_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_narrative_drift_event

            append_narrative_drift_event(session_id, drift=drift)
        except Exception:
            pass


narrative_continuity_runtime = NarrativeContinuityRuntime()
