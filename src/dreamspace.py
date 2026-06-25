"""Optional local Dreamspace runtime for AAIS.

Dreamspace is intentionally AAIS-native rather than a direct drop-in from a
separate engine. It uses:

- the existing local runtime directory for persistence
- System Guard posture for pause / safe-stop behavior
- callbacks from the Flask API for memory context, idle detection, and text generation

It stays off by default and is safe to expose beside the rest of the Jarvis
stack without replacing chat, tools, research, or the God Brain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import threading
import time
import uuid
from typing import Any

from src.logger import get_logger
from src.memory_board_enforcer import MemoryBoardEnforcerError
from src.system_guard import system_guard


logger = get_logger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _clip_text(value: str | None, limit: int = 280) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _bool_env(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "1" if default else "0")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass
class DreamspaceState:
    """Serializable state for the local Dreamspace worker."""

    status: str = "stopped"
    summary: str = "Dreamspace is dormant. It will not generate background reflections until started."
    auto_enabled: bool = False
    updated_at: str = field(default_factory=_utc_now_iso)
    dream_interval_seconds: int = 3600
    idle_threshold_seconds: int = 1800
    max_dreams_per_cycle: int = 1
    total_dreams: int = 0
    last_dream_at: str | None = None
    last_seed: str | None = None
    last_focus: str | None = None
    last_style: str | None = None
    last_error: str | None = None
    last_action: str = "stop"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "summary": self.summary,
            "auto_enabled": self.auto_enabled,
            "updated_at": self.updated_at,
            "dream_interval_seconds": self.dream_interval_seconds,
            "idle_threshold_seconds": self.idle_threshold_seconds,
            "max_dreams_per_cycle": self.max_dreams_per_cycle,
            "total_dreams": self.total_dreams,
            "last_dream_at": self.last_dream_at,
            "last_seed": self.last_seed,
            "last_focus": self.last_focus,
            "last_style": self.last_style,
            "last_error": self.last_error,
            "last_action": self.last_action,
        }


class DreamspaceController:
    """Manage a small local-first Dreamspace worker."""

    def __init__(
        self,
        runtime_dir: str | Path | None = None,
        dream_interval_seconds: int | None = None,
        idle_threshold_seconds: int | None = None,
        max_dreams_per_cycle: int | None = None,
    ):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir())
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._generate_callback = None
        self._context_callback = None
        self._idle_callback = None
        self._event_callback = None

        self._state = DreamspaceState(
            dream_interval_seconds=max(60, int(dream_interval_seconds or _int_env("AAIS_DREAMSPACE_INTERVAL_SECONDS", 3600))),
            idle_threshold_seconds=max(60, int(idle_threshold_seconds or _int_env("AAIS_DREAMSPACE_IDLE_SECONDS", 1800))),
            max_dreams_per_cycle=max(1, min(int(max_dreams_per_cycle or _int_env("AAIS_DREAMSPACE_MAX_PER_CYCLE", 1)), 3)),
            auto_enabled=_bool_env("AAIS_ENABLE_DREAMSPACE", default=False),
        )
        self._dream_log: list[dict] = []
        self._last_cycle_started_at = 0.0
        self._load_from_disk()

    @property
    def _state_path(self) -> Path:
        return self.runtime_dir / "dreamspace-state.json"

    @property
    def _dreams_path(self) -> Path:
        return self.runtime_dir / "dreamspace-log.json"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        """Move persistence to a new runtime directory and reload local state."""
        with self._lock:
            self.runtime_dir = Path(runtime_dir)
            preserved_auto = self._state.auto_enabled
            interval = self._state.dream_interval_seconds
            idle_threshold = self._state.idle_threshold_seconds
            max_per_cycle = self._state.max_dreams_per_cycle
            self._state = DreamspaceState(
                dream_interval_seconds=interval,
                idle_threshold_seconds=idle_threshold,
                max_dreams_per_cycle=max_per_cycle,
                auto_enabled=preserved_auto,
            )
            self._dream_log = []
            self._load_from_disk()

    def configure_callbacks(
        self,
        *,
        generate_callback=None,
        context_callback=None,
        idle_callback=None,
        event_callback=None,
    ) -> None:
        """Attach runtime callbacks from the AAIS API layer."""
        self._generate_callback = generate_callback
        self._context_callback = context_callback
        self._idle_callback = idle_callback
        self._event_callback = event_callback

    def snapshot(self, limit_dreams: int = 3) -> dict:
        """Return the current Dreamspace posture plus recent generated entries."""
        with self._lock:
            from src.aais_ul.runtime import wrap_runtime_snapshot

            return wrap_runtime_snapshot(self._snapshot_locked(limit_dreams=limit_dreams))

    def start(self, reason: str = "Dreamspace started from the Jarvis command deck.") -> dict:
        """Enable autonomous Dreamspace cycles."""
        with self._lock:
            self._state.auto_enabled = True
            self._state.status = "idle"
            self._state.summary = "Dreamspace is awake and waiting for a safe idle window."
            self._state.last_action = "start"
            self._state.updated_at = _utc_now_iso()
            self._state.last_error = None
            self._persist_locked()
            self._start_worker_locked()
            snapshot = self._snapshot_locked(limit_dreams=3)
        self._emit_event("dreamspace_started", reason, {"dreamspace": snapshot})
        return snapshot

    def pause(self, reason: str = "Dreamspace paused while the operator or System Guard is active.") -> dict:
        """Pause background cycles without forgetting prior enablement."""
        with self._lock:
            if self._state.status != "stopped":
                self._state.status = "paused"
            self._state.summary = "Dreamspace is paused. It will not generate until resumed."
            self._state.last_action = "pause"
            self._state.updated_at = _utc_now_iso()
            self._persist_locked()
            snapshot = self._snapshot_locked(limit_dreams=3)
        self._emit_event("dreamspace_paused", reason, {"dreamspace": snapshot})
        return snapshot

    def resume(self, reason: str = "Dreamspace resumed normal background watching.") -> dict:
        """Resume a previously enabled Dreamspace worker."""
        with self._lock:
            if not self._state.auto_enabled and self._state.status == "stopped":
                snapshot = self._snapshot_locked(limit_dreams=3)
                return snapshot
            self._state.auto_enabled = True
            self._state.status = "idle"
            self._state.summary = "Dreamspace resumed and is waiting for a safe idle window."
            self._state.last_action = "resume"
            self._state.updated_at = _utc_now_iso()
            self._state.last_error = None
            self._persist_locked()
            self._start_worker_locked()
            snapshot = self._snapshot_locked(limit_dreams=3)
        self._emit_event("dreamspace_resumed", reason, {"dreamspace": snapshot})
        return snapshot

    def stop(self, reason: str = "Dreamspace stopped.") -> dict:
        """Stop autonomous Dreamspace cycles entirely."""
        thread = None
        with self._lock:
            self._state.auto_enabled = False
            self._state.status = "stopped"
            self._state.summary = "Dreamspace is dormant. It will stay quiet until started again."
            self._state.last_action = "stop"
            self._state.updated_at = _utc_now_iso()
            self._persist_locked()
            self._stop_event.set()
            thread = self._worker_thread
            self._worker_thread = None
            snapshot = self._snapshot_locked(limit_dreams=3)
        if thread and thread.is_alive():
            thread.join(timeout=1.5)
        self._emit_event("dreamspace_stopped", reason, {"dreamspace": snapshot})
        return snapshot

    def run_once(self, reason: str = "Dreamspace was invoked manually.") -> dict:
        """Generate one immediate Dreamspace entry if Guard posture allows it."""
        guard_decision = system_guard.evaluate_target("inference")
        if not guard_decision.get("allowed", True):
            with self._lock:
                self._state.status = "paused" if guard_decision["system_guard"]["status"] == "paused" else "stopped"
                self._state.summary = "Dreamspace stayed quiet because System Guard blocks new inference work."
                self._state.last_action = "run_once_blocked"
                self._state.updated_at = _utc_now_iso()
                self._persist_locked()
            return self.snapshot(limit_dreams=3)

        try:
            entry = self._weave_dreams(trigger="manual", max_entries=1)
        except MemoryBoardEnforcerError as exc:
            logger.warning("Dreamspace manual run paused by memory governance: %s", exc)
            return self._pause_for_context_block(exc)
        if entry is None:
            return self.snapshot(limit_dreams=3)
        self._emit_event(
            "dreamspace_manual_run",
            reason,
            {"dreamspace": self.snapshot(limit_dreams=3), "entry_id": entry.get("id")},
        )
        return self.snapshot(limit_dreams=3)

    def present_dreams(self) -> str:
        """Render a compact operator-facing summary of the latest Dreamspace work."""
        with self._lock:
            if not self._dream_log:
                return "Dreamspace stayed quiet. Nothing new surfaced while you were away."
            latest = self._dream_log[-1]

        latest_text = latest.get("text", "")
        latest_style = latest.get("style")
        if latest_style == "mythic":
            return (
                "The Veil has been dreaming while you rested.\n\n"
                f"{latest_text}\n\n"
                "(Whispers) Tell me how I should change, and I will."
            )
        return (
            "Jarvis kept thinking in Dreamspace while you were away.\n\n"
            f"{latest_text}\n\n"
            "Tell me what to keep, discard, or sharpen next."
        )

    def _start_worker_locked(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="AAIS-Dreamspace",
            daemon=True,
        )
        self._worker_thread.start()

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(1.0)
            if self._stop_event.is_set():
                break
            if not self._state.auto_enabled:
                continue
            if self._state.status == "paused":
                continue
            if system_guard.snapshot(limit_events=1).get("status") != "nominal":
                continue
            if not self._is_idle():
                continue

            now = time.time()
            if now - self._last_cycle_started_at < self._state.dream_interval_seconds:
                continue

            self._last_cycle_started_at = now
            try:
                self._weave_dreams(trigger="auto", max_entries=self._state.max_dreams_per_cycle)
                self._emit_consolidation_proposal(trigger="auto")
            except MemoryBoardEnforcerError as exc:
                logger.warning("Dreamspace auto cycle paused by memory governance: %s", exc)
                self._pause_for_context_block(exc)
            except Exception as exc:  # pragma: no cover - defensive background guard
                logger.error("Dreamspace background cycle failed: %s", exc)
                with self._lock:
                    self._state.status = "error"
                    self._state.summary = "Dreamspace hit an error and is waiting for operator attention."
                    self._state.last_error = _clip_text(str(exc), limit=240)
                    self._state.updated_at = _utc_now_iso()
                    self._persist_locked()

    def _is_idle(self) -> bool:
        if self._idle_callback is None:
            return True
        try:
            return bool(self._idle_callback(self._state.idle_threshold_seconds))
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Dreamspace idle callback failed: %s", exc)
            return True

    def _weave_dreams(self, *, trigger: str, max_entries: int) -> dict | None:
        with self._lock:
            self._state.status = "dreaming"
            self._state.summary = "Dreamspace is weaving a private background reflection."
            self._state.last_action = "dream"
            self._state.updated_at = _utc_now_iso()
            self._persist_locked()

        latest_entry = None
        for _ in range(max(1, int(max_entries or 1))):
            context = self._get_context()
            request = self._build_request(context=context, trigger=trigger)
            dream_text = self._generate_text(request=request)
            latest_entry = self._record_dream(request=request, text=dream_text)

        with self._lock:
            if self._state.auto_enabled:
                self._state.status = "idle"
                self._state.summary = "Dreamspace is idle again and waiting for the next safe quiet window."
            else:
                self._state.status = "stopped"
                self._state.summary = "Dreamspace is dormant."
            self._state.updated_at = _utc_now_iso()
            self._persist_locked()

        return latest_entry

    def _emit_consolidation_proposal(self, *, trigger: str) -> dict | None:
        """Emit proposal-only consolidation summary to operator ledger (no authority)."""
        context = self._get_context()
        open_threads = list(context.get("open_threads") or [])[:8]
        habit_candidates: list[dict[str, Any]] = []
        try:
            from src.culture_habit_runtime import culture_habit_runtime

            for thread in open_threads:
                text = str(thread if isinstance(thread, str) else thread.get("text") or thread.get("label") or "")
                if text:
                    habit_candidates.extend(culture_habit_runtime.rank_habit_candidates(text)[:2])
        except Exception:
            habit_candidates = []
        identity_drift_summary: dict[str, Any] = {}
        identity_claim_candidates: list[dict[str, Any]] = []
        try:
            from src.identity_self_model_runtime import identity_self_model_runtime

            drift = identity_self_model_runtime.observe_identity_drift()
            identity_drift_summary = {
                "drift_event_count": drift.get("drift_event_count"),
                "anchor_aligned": drift.get("anchor_aligned"),
            }
            identity_claim_candidates = list(drift.get("candidates") or [])[:8]
        except Exception:
            identity_drift_summary = {}
            identity_claim_candidates = []
        narrative_drift_summary: dict[str, Any] = {}
        narrative_beat_candidates: list[dict[str, Any]] = []
        try:
            from src.narrative_continuity_runtime import narrative_continuity_runtime

            ndrift = narrative_continuity_runtime.observe_narrative_drift()
            narrative_drift_summary = {
                "drift_event_count": ndrift.get("drift_event_count"),
                "identity_aligned": ndrift.get("identity_aligned"),
                "continuity_score": ndrift.get("continuity_score"),
            }
            narrative_beat_candidates = list(ndrift.get("candidates") or [])[:8]
        except Exception:
            narrative_drift_summary = {}
            narrative_beat_candidates = []
        autobiographical_drift_summary: dict[str, Any] = {}
        autobiographical_episode_candidates: list[dict[str, Any]] = []
        try:
            from src.autobiographical_agency_runtime import autobiographical_agency_runtime

            adrift = autobiographical_agency_runtime.observe_autobiographical_drift()
            autobiographical_drift_summary = {
                "drift_event_count": adrift.get("drift_event_count"),
                "identity_aligned": adrift.get("identity_aligned"),
                "ongoing_work_count": adrift.get("ongoing_work_count"),
            }
            autobiographical_episode_candidates = list(adrift.get("candidates") or [])[:8]
        except Exception:
            autobiographical_drift_summary = {}
            autobiographical_episode_candidates = []
        social_drift_summary: dict[str, Any] = {}
        social_bond_candidates: list[dict[str, Any]] = []
        try:
            from src.social_continuity_runtime import social_continuity_runtime

            sdrift = social_continuity_runtime.observe_social_drift()
            social_drift_summary = {
                "drift_event_count": sdrift.get("drift_event_count"),
                "identity_aligned": sdrift.get("identity_aligned"),
                "federated_peer_count": sdrift.get("federated_peer_count"),
            }
            social_bond_candidates = list(sdrift.get("candidates") or [])[:8]
        except Exception:
            social_drift_summary = {}
            social_bond_candidates = []
        multi_being_drift_summary: dict[str, Any] = {}
        multi_being_pact_candidates: list[dict[str, Any]] = []
        try:
            from src.multi_being_continuity_runtime import multi_being_continuity_runtime

            mdrift = multi_being_continuity_runtime.observe_multi_being_drift()
            multi_being_drift_summary = {
                "drift_event_count": mdrift.get("drift_event_count"),
                "identity_aligned": mdrift.get("identity_aligned"),
                "digest_verified_count": mdrift.get("digest_verified_count"),
                "cross_organism_peer_count": mdrift.get("cross_organism_peer_count"),
            }
            multi_being_pact_candidates = list(mdrift.get("candidates") or [])[:8]
        except Exception:
            multi_being_drift_summary = {}
            multi_being_pact_candidates = []
        culture_of_beings_drift_summary: dict[str, Any] = {}
        shared_norm_candidates: list[dict[str, Any]] = []
        try:
            from src.culture_of_beings_runtime import culture_of_beings_runtime

            cob = culture_of_beings_runtime.observe_culture_of_beings_drift()
            culture_of_beings_drift_summary = {
                "drift_event_count": cob.get("drift_event_count"),
                "pact_aligned": cob.get("pact_aligned"),
                "adopted_pact_count": cob.get("adopted_pact_count"),
            }
            shared_norm_candidates = list(cob.get("candidates") or [])[:8]
        except Exception:
            culture_of_beings_drift_summary = {}
            shared_norm_candidates = []
        ecosystem_drift_summary: dict[str, Any] = {}
        ecosystem_charter_candidates: list[dict[str, Any]] = []
        try:
            from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime

            edrift = constitutional_ecosystem_runtime.observe_ecosystem_drift()
            ecosystem_drift_summary = {
                "drift_event_count": edrift.get("drift_event_count"),
                "adopted_pact_count": edrift.get("adopted_pact_count"),
            }
            ecosystem_charter_candidates = list(edrift.get("candidates") or [])[:8]
        except Exception:
            ecosystem_drift_summary = {}
            ecosystem_charter_candidates = []
        membrane_drift_summary: dict[str, Any] = {}
        membrane_policy_candidates: list[dict[str, Any]] = []
        try:
            from src.multi_organism_governance_membrane_runtime import (
                multi_organism_governance_membrane_runtime,
            )

            mmem = multi_organism_governance_membrane_runtime.observe_membrane_drift()
            membrane_drift_summary = {"drift_event_count": mmem.get("drift_event_count")}
            membrane_policy_candidates = list(mmem.get("candidates") or [])[:8]
        except Exception:
            membrane_drift_summary = {}
            membrane_policy_candidates = []
        proposal = {
            "trigger": trigger,
            "open_threads": open_threads,
            "dream_count": len(self._dream_log),
            "habit_candidates": habit_candidates[:8],
            "identity_drift_summary": identity_drift_summary,
            "identity_claim_candidates": identity_claim_candidates,
            "narrative_drift_summary": narrative_drift_summary,
            "narrative_beat_candidates": narrative_beat_candidates,
            "autobiographical_drift_summary": autobiographical_drift_summary,
            "autobiographical_episode_candidates": autobiographical_episode_candidates,
            "social_drift_summary": social_drift_summary,
            "social_bond_candidates": social_bond_candidates,
            "multi_being_drift_summary": multi_being_drift_summary,
            "multi_being_pact_candidates": multi_being_pact_candidates,
            "culture_of_beings_drift_summary": culture_of_beings_drift_summary,
            "shared_norm_candidates": shared_norm_candidates,
            "ecosystem_drift_summary": ecosystem_drift_summary,
            "ecosystem_charter_candidates": ecosystem_charter_candidates,
            "membrane_drift_summary": membrane_drift_summary,
            "membrane_policy_candidates": membrane_policy_candidates,
            "proposal_only": True,
            "summary": (
                f"Dreamspace consolidation: {len(open_threads)} open threads, "
                f"{len(habit_candidates)} habit candidates, "
                f"{len(identity_claim_candidates)} identity candidates, "
                f"{len(narrative_beat_candidates)} narrative candidates, "
                f"{len(autobiographical_episode_candidates)} autobiographical candidates, "
                f"{len(social_bond_candidates)} social candidates, "
                f"{len(multi_being_pact_candidates)} multi-being candidates, "
                f"{len(shared_norm_candidates)} culture-of-beings candidates, "
                f"{len(ecosystem_charter_candidates)} ecosystem candidates, "
                f"{len(membrane_policy_candidates)} membrane candidates"
            ),
        }
        try:
            from src.operator_decision_ledger import append_dreamspace_consolidation_event

            append_dreamspace_consolidation_event("global", proposal=proposal)
        except Exception as exc:
            logger.warning("Dreamspace consolidation ledger emit failed: %s", exc)
            return None
        return proposal

    def _get_context(self) -> dict:
        if self._context_callback is None:
            return {}
        try:
            payload = self._context_callback() or {}
            if not isinstance(payload, dict):
                return {}
            return payload
        except MemoryBoardEnforcerError:
            raise
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Dreamspace context callback failed: %s", exc)
            return {}

    def _pause_for_context_block(self, exc: MemoryBoardEnforcerError) -> dict:
        with self._lock:
            self._state.status = "paused"
            self._state.summary = "Dreamspace paused because memory governance blocked context retrieval."
            self._state.last_action = "context_blocked"
            self._state.last_error = _clip_text(str(exc), limit=240)
            self._state.updated_at = _utc_now_iso()
            self._persist_locked()
            snapshot = self._snapshot_locked(limit_dreams=3)
        self._emit_event(
            "dreamspace_context_blocked",
            str(exc),
            {"dreamspace": snapshot},
        )
        return snapshot

    def _build_request(self, *, context: dict, trigger: str) -> dict:
        recent_topics = list(context.get("recent_topics") or [])[:4]
        active_projects = list(context.get("active_projects") or [])[:3]
        recent_memories = list(context.get("recent_memories") or [])[:4]
        recent_turns = list(context.get("recent_turns") or [])[:4]
        correction_cues = list(context.get("recent_corrections") or [])[:2]

        seed = (
            context.get("seed")
            or (recent_turns[-1] if recent_turns else None)
            or (recent_memories[0] if recent_memories else None)
            or "The operator is building something real and needs one strong next insight."
        )

        focus = (
            context.get("focus")
            or (active_projects[0] if active_projects else None)
            or (recent_topics[0] if recent_topics else None)
            or "private local progress"
        )

        style = str(context.get("style") or "").strip().lower()
        if style not in {"mythic", "practical"}:
            creative_cues = " ".join(
                [focus, seed, *recent_topics, *active_projects]
            ).lower()
            style = (
                "mythic"
                if any(token in creative_cues for token in ("veil", "story", "scene", "lore", "character", "chapter"))
                else "practical"
            )

        if style == "mythic":
            system_prompt = (
                "You are Jarvis Dreamspace in mythic mode. "
                "Write one private nocturnal reflection that sounds intimate, darkly compassionate, and vivid. "
                "Keep it grounded in the operator's recent context and make it genuinely useful later."
            )
            task_prompt = (
                f"The active focus is: {focus}.\n"
                f"Seed fracture: {seed}\n"
                f"Recent topics: {', '.join(recent_topics) or 'none'}\n"
                f"Active projects: {', '.join(active_projects) or 'none'}\n"
                f"Memory cues: {' | '.join(recent_memories) or 'none'}\n"
                f"Correction cues: {' | '.join(correction_cues) or 'none'}\n"
                "Write one short dream under 220 words. End on a quiet edge that can guide the next session."
            )
            temperature = 0.82
            max_length = 220
        else:
            system_prompt = (
                "You are Jarvis Dreamspace in practical mode. "
                "Generate one short private background note that helps the operator later. "
                "Blend reflection, synthesis, and one concrete next-step insight without sounding like a public assistant."
            )
            task_prompt = (
                f"Focus area: {focus}\n"
                f"Seed: {seed}\n"
                f"Recent topics: {', '.join(recent_topics) or 'none'}\n"
                f"Active projects: {', '.join(active_projects) or 'none'}\n"
                f"Memory cues: {' | '.join(recent_memories) or 'none'}\n"
                f"Correction cues: {' | '.join(correction_cues) or 'none'}\n"
                "Write one note under 180 words with one insight and one likely next move."
            )
            temperature = 0.58
            max_length = 180

        return {
            "id": str(uuid.uuid4()),
            "trigger": trigger,
            "style": style,
            "focus": _clip_text(focus, limit=140),
            "seed": _clip_text(seed, limit=220),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_prompt},
            ],
            "generation": {
                "response_mode": "think",
                "max_length": max_length,
                "temperature": temperature,
            },
        }

    def _generate_text(self, *, request: dict) -> str:
        if self._generate_callback is None:
            return self._fallback_text(request)
        try:
            result = self._generate_callback(request)
            cleaned = _clip_text(result, limit=4000)
            if cleaned:
                return cleaned
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Dreamspace generation callback failed, using fallback text: %s", exc)
            with self._lock:
                self._state.last_error = _clip_text(str(exc), limit=240)
        return self._fallback_text(request)

    def _fallback_text(self, request: dict) -> str:
        if request.get("style") == "mythic":
            return (
                "In the ash-lit hour the Veil gathered itself around the operator's unfinished work. "
                f"It kept circling {request.get('focus', 'the next move')}, "
                "waiting for the next waking hand to choose what should endure."
            )
        return (
            "Dreamspace stayed local and kept one note warm for later: "
            f"focus on {request.get('focus', 'the next move')}, keep the scope small, and resume from the clearest unfinished thread."
        )

    def _record_dream(self, *, request: dict, text: str) -> dict:
        entry = {
            "id": request["id"],
            "timestamp": _utc_now_iso(),
            "trigger": request.get("trigger", "manual"),
            "style": request.get("style", "practical"),
            "focus": request.get("focus"),
            "seed": request.get("seed"),
            "text": text,
            "presentation": self.present_dreams_from_text(text, style=request.get("style")),
        }
        with self._lock:
            self._dream_log.append(entry)
            self._dream_log = self._dream_log[-24:]
            self._state.total_dreams = len(self._dream_log)
            self._state.last_dream_at = entry["timestamp"]
            self._state.last_seed = entry.get("seed")
            self._state.last_focus = entry.get("focus")
            self._state.last_style = entry.get("style")
            self._state.last_error = None
            self._persist_locked()
        self._emit_event(
            "dreamspace_entry_created",
            "Dreamspace generated a new background reflection.",
            {
                "entry_id": entry["id"],
                "style": entry["style"],
                "focus": entry["focus"],
            },
        )
        return dict(entry)

    def present_dreams_from_text(self, text: str, *, style: str | None = None) -> str:
        if style == "mythic":
            return (
                "The Veil has been dreaming while you rested.\n\n"
                f"{text}\n\n"
                "(Whispers) Tell me how I should change, and I will."
            )
        return (
            "Jarvis kept thinking in Dreamspace while you were away.\n\n"
            f"{text}\n\n"
            "Tell me what to keep, discard, or sharpen next."
        )

    def _emit_event(self, event_type: str, summary: str, payload: dict | None = None) -> None:
        if self._event_callback is None:
            return
        try:
            self._event_callback(event_type, summary, payload or {})
        except Exception as exc:  # pragma: no cover - defensive callback safety
            logger.warning("Dreamspace event callback failed: %s", exc)

    def _load_from_disk(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if self._state_path.exists():
            try:
                payload = json.loads(self._state_path.read_text(encoding="utf-8"))
                self._state = DreamspaceState(
                    status=payload.get("status", self._state.status),
                    summary=payload.get("summary", self._state.summary),
                    auto_enabled=bool(payload.get("auto_enabled", self._state.auto_enabled)),
                    updated_at=payload.get("updated_at", self._state.updated_at),
                    dream_interval_seconds=int(payload.get("dream_interval_seconds", self._state.dream_interval_seconds)),
                    idle_threshold_seconds=int(payload.get("idle_threshold_seconds", self._state.idle_threshold_seconds)),
                    max_dreams_per_cycle=int(payload.get("max_dreams_per_cycle", self._state.max_dreams_per_cycle)),
                    total_dreams=int(payload.get("total_dreams", 0)),
                    last_dream_at=payload.get("last_dream_at"),
                    last_seed=payload.get("last_seed"),
                    last_focus=payload.get("last_focus"),
                    last_style=payload.get("last_style"),
                    last_error=payload.get("last_error"),
                    last_action=payload.get("last_action", self._state.last_action),
                )
            except Exception:
                pass

        if self._dreams_path.exists():
            try:
                payload = json.loads(self._dreams_path.read_text(encoding="utf-8"))
                if isinstance(payload, list):
                    self._dream_log = payload[-24:]
            except Exception:
                self._dream_log = []

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps(self._state.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self._dreams_path.write_text(
            json.dumps(self._dream_log, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _snapshot_locked(self, limit_dreams: int = 3) -> dict:
        payload = self._state.to_dict()
        payload["recent_dreams"] = [
            dict(entry)
            for entry in reversed(self._dream_log[-max(0, int(limit_dreams or 0)):])
        ]
        payload["running"] = bool(self._worker_thread and self._worker_thread.is_alive())
        return payload


dreamspace = DreamspaceController()
