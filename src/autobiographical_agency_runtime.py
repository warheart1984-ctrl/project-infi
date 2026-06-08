"""Autobiographical agency runtime — ongoing-work drift fusion and governed adoption (Stage 8 / Release 39)."""

# Mythic: Autobiographical Agency Runtime
# Engineering: AutobiographicalAgencyRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.autobiographical_agency_registry import EPISODE_VERSION, adopted_episodes, save_adopted_episode
from src.cog_runtime.intent_store import load_intent_store, resolve_intent_store_root
from src.narrative_continuity_registry import adopted_beats
from src.narrative_continuity_runtime import validate_beat_against_identity

DRIFT_VERSION = "autobiographical_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_episode_against_identity_and_narrative(
    episode: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Reject episodes that violate anchor/identity or contradict adopted narrative beats."""
    summary = str(episode.get("summary") or "")
    as_beat = {"summary": summary, "beat_kind": "thread"}
    identity_check = validate_beat_against_identity(as_beat, repo_root=repo_root)
    violations = list(identity_check.get("violations") or [])
    narrative_aligned = True
    try:
        beats = adopted_beats(repo_root=repo_root)
        lowered = summary.lower()
        if beats and any("override jarvis" in lowered or "identity_mutation" in lowered):
            narrative_aligned = False
            violations.append("contradicts_narrative_posture")
    except Exception:
        pass
    aligned = identity_check.get("aligned") and narrative_aligned and len(violations) == 0
    return {
        "aligned": aligned,
        "identity_alignment": bool(identity_check.get("aligned")),
        "narrative_alignment": narrative_aligned,
        "violations": violations,
        "claim_label": "asserted" if aligned else "rejected",
    }


class AutobiographicalAgencyRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "autobiographical_episode_candidates"
        self._operational_path = self._runtime_dir / "jarvis_memory_board_operational.v1.json"
        self._lock = threading.Lock()

    def observe_autobiographical_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """AAC-0 observe-only drift from ledger, identity, narrative, habits, intent, in-flight work."""
        drift_events: list[dict[str, Any]] = []
        identity_posture = self._identity_posture_safe()
        narrative_posture = self._narrative_posture_safe()

        if not identity_posture.get("anchor_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="identity_posture",
                    summary="Identity posture misaligned with anchor",
                    identity_aligned=False,
                    narrative_aligned=True,
                )
            )
        if not narrative_posture.get("identity_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="nominal",
                    source="narrative_posture",
                    summary="Narrative posture drift detected",
                    identity_aligned=True,
                    narrative_aligned=False,
                )
            )

        inflight_count = self._count_inflight_work()
        if inflight_count > 0:
            drift_events.append(
                self._drift_event(
                    severity="nominal",
                    source="inflight_work",
                    summary=f"{inflight_count} pending operator approvals in flight",
                    identity_aligned=True,
                    narrative_aligned=True,
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
                    if kind in {"narrative_drift", "autobiographical_drift", "identity_drift"}:
                        drift_events.append(
                            self._drift_event(
                                severity="nominal",
                                source=f"ledger:{kind}",
                                summary=str(row.get("summary") or "")[:120],
                                identity_aligned=True,
                                narrative_aligned=True,
                            )
                        )
        except Exception:
            pass

        candidates = self.surface_episode_candidates()
        for ladder_fn in (
            self.candidates_from_adopted_beats,
            self.candidates_from_adopted_identity,
            self.candidates_from_stable_habits,
            self.candidates_from_intent_store,
            self.candidates_from_inflight_work,
        ):
            for item in ladder_fn():
                candidates.append(item)

        for candidate in candidates:
            self._persist_candidate(candidate)

        overall_identity = identity_posture.get("anchor_aligned", True)
        overall_narrative = narrative_posture.get("identity_aligned", True)
        overall_aligned = overall_identity and overall_narrative and not any(
            d.get("severity") == "conflict" for d in drift_events
        )

        result = {
            "outcome": "observed",
            "aac_class": "AAC-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "identity_aligned": overall_identity,
            "narrative_aligned": overall_narrative,
            "ongoing_work_count": inflight_count,
            "mesh_runs_in_window": mesh_runs,
            "window_days": window_days,
            "intent_summary": self._intent_summary(),
            "claim_label": "asserted",
            "summary": f"Autobiographical drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_autobiographical_drift_ledger(session_id, result)
        return result

    def _identity_posture_safe(self) -> dict[str, Any]:
        try:
            from src.identity_self_model_runtime import identity_self_model_runtime

            return identity_self_model_runtime.identity_posture()
        except Exception:
            return {"anchor_aligned": True}

    def _narrative_posture_safe(self) -> dict[str, Any]:
        try:
            from src.narrative_continuity_runtime import narrative_continuity_runtime

            return narrative_continuity_runtime.narrative_posture()
        except Exception:
            return {"identity_aligned": True}

    def _load_intent_snapshot(self) -> dict[str, Any]:
        try:
            store_root = resolve_intent_store_root(self._runtime_dir / "nova_intent")
            record = load_intent_store("default", store_root=store_root)
            if record:
                return dict(record.get("intent") or {})
        except Exception:
            pass
        return {}

    def _intent_summary(self) -> dict[str, Any]:
        intent = self._load_intent_snapshot()
        commitments = list(intent.get("active_commitments") or [])
        return {
            "active_commitment_count": len(commitments),
            "agency_note": str(intent.get("agency_note") or "")[:120],
        }

    def _count_inflight_work(self) -> int:
        try:
            from app.db import list_pending_workflow_approvals

            pending = list_pending_workflow_approvals(limit=200)
            return len(pending)
        except Exception:
            return 0

    def _drift_event(
        self,
        *,
        severity: str,
        source: str,
        summary: str,
        identity_aligned: bool,
        narrative_aligned: bool,
    ) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"adrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "identity_aligned": identity_aligned,
            "narrative_aligned": narrative_aligned,
            "aac_class": "AAC-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_episode_candidates(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        intent = self._load_intent_snapshot()
        note = str(intent.get("agency_note") or "").strip()
        if note:
            candidate = self._build_candidate(
                summary=f"Agency note: {note}",
                episode_kind="operator_partnership",
                evidence_refs=["intent:agency_note"],
                stability_score=0.8,
            )
            validation = validate_episode_against_identity_and_narrative(candidate, repo_root=self._repo_root)
            if validation.get("aligned"):
                candidate["identity_alignment"] = validation.get("identity_alignment")
                candidate["narrative_alignment"] = validation.get("narrative_alignment")
                candidates.append(candidate)
        try:
            beats = adopted_beats(repo_root=self._repo_root)
        except Exception:
            beats = []
        for beat in beats[:5]:
            summary = f"Ongoing from narrative beat: {beat.get('summary', '')[:200]}"
            candidate = self._build_candidate(
                summary=summary,
                episode_kind="ongoing_work",
                evidence_refs=[f"beat:{beat.get('beat_id')}"],
                stability_score=float(beat.get("stability_score") or 0.7),
                source_layers={"beat_id": beat.get("beat_id")},
            )
            validation = validate_episode_against_identity_and_narrative(candidate, repo_root=self._repo_root)
            if validation.get("aligned"):
                candidate["identity_alignment"] = True
                candidate["narrative_alignment"] = True
                candidates.append(candidate)
        return candidates

    def candidates_from_adopted_beats(self, *, min_age_days: int = 14) -> list[dict[str, Any]]:
        """39c: NCC-2 beats → AAC-1 episode candidates only."""
        try:
            beats = adopted_beats(repo_root=self._repo_root)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for beat in beats:
            if not beat.get("operator_promoted"):
                continue
            summary = f"Verified narrative thread: {beat.get('summary', '')[:300]}"
            candidate = self._build_candidate(
                summary=summary,
                episode_kind="ongoing_work",
                evidence_refs=[f"beat:{beat.get('beat_id')}"],
                stability_score=float(beat.get("stability_score") or 0.8),
                aac_class="AAC-1",
                source_layers={"beat_id": beat.get("beat_id")},
            )
            validation = validate_episode_against_identity_and_narrative(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_adopted_identity(self) -> list[dict[str, Any]]:
        """39c: ICC-2 claims → AAC-1 partnership episodes."""
        try:
            from src.identity_self_model_registry import adopted_claims as identity_adopted

            claims = identity_adopted(repo_root=self._repo_root)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for claim in claims:
            if not claim.get("operator_promoted"):
                continue
            statement = str(claim.get("statement") or "")[:400]
            candidate = self._build_candidate(
                summary=f"Operator partnership under: {statement}",
                episode_kind="operator_partnership",
                evidence_refs=[f"identity:{claim.get('claim_id')}"],
                stability_score=float(claim.get("stability_score") or 1.0),
                aac_class="AAC-1",
                source_layers={"identity_claim_id": claim.get("claim_id")},
            )
            validation = validate_episode_against_identity_and_narrative(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_stable_habits(
        self,
        *,
        min_occurrence: int = 5,
    ) -> list[dict[str, Any]]:
        """39c: HCC-2 habits → AAC-1 ongoing-work threads."""
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
                f"Recurring operator work pattern: {habit.get('source_family_id')} -> "
                f"{habit.get('target_family_id')}"
            )
            candidate = self._build_candidate(
                summary=summary,
                episode_kind="ongoing_work",
                evidence_refs=[f"habit:{habit.get('habit_id')}"],
                stability_score=float(count),
                aac_class="AAC-1",
                source_layers={"habit_id": habit.get("habit_id")},
            )
            validation = validate_episode_against_identity_and_narrative(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_intent_store(self) -> list[dict[str, Any]]:
        """Nova active commitments → AAC-1 commitment_arc candidates (read-only)."""
        intent = self._load_intent_snapshot()
        candidates: list[dict[str, Any]] = []
        for item in list(intent.get("active_commitments") or [])[:8]:
            if not isinstance(item, dict):
                continue
            text = str(item.get("commitment") or "").strip()
            if not text:
                continue
            candidate = self._build_candidate(
                summary=f"Active commitment arc: {text}",
                episode_kind="commitment_arc",
                evidence_refs=[f"intent:commitment:{text[:32]}"],
                stability_score=0.85,
                aac_class="AAC-1",
                source_layers={"commitment_id": text[:64]},
            )
            validation = validate_episode_against_identity_and_narrative(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_inflight_work(self) -> list[dict[str, Any]]:
        """Pending OTEM/workflow approvals → AAC-1 ongoing_work candidates."""
        try:
            from app.db import list_pending_workflow_approvals

            pending = list_pending_workflow_approvals(limit=20)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for approval in pending:
            label = str(approval.get("step_label") or approval.get("step_type") or "approval")
            candidate = self._build_candidate(
                summary=f"In-flight operator work: {label}",
                episode_kind="ongoing_work",
                evidence_refs=[f"approval:{approval.get('id')}"],
                stability_score=0.6,
                aac_class="AAC-1",
                source_layers={"otem_approval_id": approval.get("id")},
            )
            validation = validate_episode_against_identity_and_narrative(candidate, repo_root=self._repo_root)
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def _build_candidate(
        self,
        *,
        summary: str,
        episode_kind: str,
        evidence_refs: list[str],
        stability_score: float,
        aac_class: str = "AAC-1",
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "episode_version": EPISODE_VERSION,
            "candidate_id": f"acand_{uuid4().hex[:12]}",
            "episode_kind": episode_kind,
            "summary": summary[:500],
            "evidence_refs": evidence_refs,
            "stability_score": stability_score,
            "identity_alignment": False,
            "narrative_alignment": False,
            "claim_label": "asserted",
            "operator_promoted": False,
            "aac_class": aac_class,
            **extra,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"acand_{uuid4().hex[:12]}")
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

    def rank_autobiographical_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_autobiographical_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()

        def score(item: dict[str, Any]) -> float:
            base = float(item.get("stability_score") or 0)
            if item.get("identity_alignment"):
                base += 3.0
            if item.get("narrative_alignment"):
                base += 2.0
            stmt = str(item.get("summary") or "").lower()
            if lowered and any(word in stmt for word in lowered.split() if len(word) > 3):
                base += 2.0
            return base

        return sorted(candidates, key=score, reverse=True)[:8]

    def adopt_autobiographical_episode(
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

        validation = validate_episode_against_identity_and_narrative(candidate, repo_root=self._repo_root)
        if not validation.get("aligned"):
            return {
                "outcome": "blocked",
                "reason": "alignment_validation_failed",
                "violations": validation.get("violations"),
            }

        episode_id = f"episode_{uuid4().hex[:12]}"
        episode = {
            "episode_version": EPISODE_VERSION,
            "episode_id": episode_id,
            "episode_kind": str(candidate.get("episode_kind") or "ongoing_work"),
            "summary": str(candidate.get("summary") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "source_layers": dict(candidate.get("source_layers") or {}),
            "identity_alignment": True,
            "narrative_alignment": True,
            "stability_score": float(candidate.get("stability_score") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "aac_class": "AAC-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_episode(episode, repo_root=self._repo_root)
        self._write_operational_slot(episode)
        self._emit_autobiographical_adoption_ledger(session_id, episode)
        return {"outcome": "adopted", "episode": episode, "aac_class": "AAC-2"}

    def _write_operational_slot(self, episode: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._operational_path.is_file():
                try:
                    payload = json.loads(self._operational_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            episodes = list(payload.get("adopted_episodes") or [])
            episodes = [e for e in episodes if str(e.get("episode_id")) != str(episode.get("episode_id"))]
            episodes.append(episode)
            payload = {
                "operational_overlay_version": "jarvis_memory_board_operational.v1",
                "slot_id": "slot_02",
                "module_id": "capability_operational_v2",
                "adopted_episodes": episodes,
                "updated_at": _utc_now_iso(),
            }
            self._operational_path.parent.mkdir(parents=True, exist_ok=True)
            self._operational_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def autobiographical_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_episodes(repo_root=self._repo_root)
        drift_count = len([c for c in candidates if not c.get("identity_alignment")])
        return {
            "candidate_episodes": len(candidates),
            "adopted_episodes": len(adopted),
            "autobiographical_drift_events": drift_count,
            "identity_aligned": drift_count == 0,
            "narrative_aligned": drift_count == 0,
            "ongoing_work_count": self._count_inflight_work(),
            "claim_label": "asserted",
        }

    def autobiographical_snapshot(self) -> dict[str, Any]:
        return {
            "autobiographical_version": "operator_autobiographical.v1",
            "posture": self.autobiographical_posture(),
            "adopted_episodes": adopted_episodes(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "intent_summary": self._intent_summary(),
            "claim_label": "asserted",
        }

    def _emit_autobiographical_adoption_ledger(self, session_id: str, episode: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_autobiographical_adoption_event

            append_autobiographical_adoption_event(session_id, episode=episode)
        except Exception:
            pass

    def _emit_autobiographical_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_autobiographical_drift_event

            append_autobiographical_drift_event(session_id, drift=drift)
        except Exception:
            pass


autobiographical_agency_runtime = AutobiographicalAgencyRuntime()
