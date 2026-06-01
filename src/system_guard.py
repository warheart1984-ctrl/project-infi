"""Local-first system guard for AAIS runtime safety.

The guard supports graded safety posture:
- pause: block new turns/actions temporarily
- safe stop: unload active runtime work without destructive teardown
- hard stop: freeze AI work, lock memory writes, and require explicit resume
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import threading
import uuid


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clip_text(value: str | None, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


@dataclass
class SystemGuardState:
    """Serializable guard posture for the local runtime."""

    status: str = "nominal"
    summary: str = "System Guard is nominal. New Jarvis turns and operator actions are allowed."
    reason: str = "system_started"
    last_action: str = "resume"
    updated_at: str = field(default_factory=_utc_now_iso)
    accepting_turns: bool = True
    accepting_actions: bool = True
    accepting_memory_writes: bool = True
    actor: str = "system"
    event_count: int = 0

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "summary": self.summary,
            "reason": self.reason,
            "last_action": self.last_action,
            "updated_at": self.updated_at,
            "accepting_turns": self.accepting_turns,
            "accepting_actions": self.accepting_actions,
            "accepting_memory_writes": self.accepting_memory_writes,
            "actor": self.actor,
            "event_count": self.event_count,
        }


class SystemGuardController:
    """Persist and enforce a lightweight operator safety posture."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir())
        self._lock = threading.Lock()
        self._state = SystemGuardState()
        self._events: list[dict] = []
        self._load_from_disk()

    @property
    def _state_path(self) -> Path:
        return self.runtime_dir / "system-guard.json"

    @property
    def _events_path(self) -> Path:
        return self.runtime_dir / "system-guard-events.jsonl"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        """Point the guard at a different runtime directory, then reload state."""
        with self._lock:
            self.runtime_dir = Path(runtime_dir)
            self._state = SystemGuardState()
            self._events = []
            self._load_from_disk()

    def reset(self, persist: bool = True) -> dict:
        """Reset the guard to a nominal state."""
        with self._lock:
            self._state = SystemGuardState()
            self._events = []
            if persist:
                self.runtime_dir.mkdir(parents=True, exist_ok=True)
                self._state_path.write_text(
                    json.dumps(self._state.to_dict(), indent=2),
                    encoding="utf-8",
                )
                self._events_path.write_text("", encoding="utf-8")
            payload = self._state.to_dict()
            payload["recent_events"] = []
            return payload

    def snapshot(self, limit_events: int = 6) -> dict:
        with self._lock:
            payload = self._state.to_dict()
            payload["recent_events"] = [
                dict(event)
                for event in reversed(self._events[-max(0, int(limit_events or 0)):])
            ]
            from src.aais_ul_substrate import wrap_runtime_snapshot

            return wrap_runtime_snapshot(payload)

    def pause(self, reason: str = "", actor: str = "operator") -> dict:
        return self._set_state(
            status="paused",
            action="pause",
            summary="System Guard is paused. New Jarvis turns and local actions are temporarily blocked.",
            reason=reason or "Operator paused AAIS.",
            actor=actor,
            accepting_turns=False,
            accepting_actions=False,
            accepting_memory_writes=True,
        )

    def safe_stop(self, reason: str = "", actor: str = "operator") -> dict:
        return self._set_state(
            status="stopped",
            action="safe_stop",
            summary="System Guard is in safe stop. The local runtime will not accept new AI work until resume.",
            reason=reason or "Operator requested a safe stop.",
            actor=actor,
            accepting_turns=False,
            accepting_actions=False,
            accepting_memory_writes=True,
        )

    def hard_stop(self, reason: str = "", actor: str = "operator") -> dict:
        return self._set_state(
            status="hard_stopped",
            action="hard_stop",
            summary="System Guard is in hard stop. New AI work is frozen, memory writes are locked, and explicit resume is required.",
            reason=reason or "Operator requested a hard stop.",
            actor=actor,
            accepting_turns=False,
            accepting_actions=False,
            accepting_memory_writes=False,
        )

    def resume(self, reason: str = "", actor: str = "operator") -> dict:
        return self._set_state(
            status="nominal",
            action="resume",
            summary="System Guard resumed normal operation. New Jarvis turns and local actions are allowed again.",
            reason=reason or "Operator resumed AAIS.",
            actor=actor,
            accepting_turns=True,
            accepting_actions=True,
            accepting_memory_writes=True,
        )

    def evaluate_target(self, target: str) -> dict:
        """Return whether the requested runtime target is currently allowed."""
        normalized_target = " ".join(str(target or "turn").lower().split()).strip().replace("-", "_")
        snapshot = self.snapshot(limit_events=3)
        status = snapshot["status"]
        if (
            status == "nominal"
            or (
                normalized_target == "memory_write"
                and snapshot.get("accepting_memory_writes", True)
            )
        ):
            return {
                "allowed": True,
                "target": normalized_target,
                "summary": "System Guard allows this request.",
                "status_code": 200,
                "system_guard": snapshot,
            }

        if normalized_target == "action":
            subject = "local actions"
        elif normalized_target == "turn":
            subject = "new Jarvis turns"
        elif normalized_target == "memory_write":
            subject = "memory writes"
        else:
            subject = "new AI work"

        if normalized_target == "memory_write":
            summary = "System Guard hard stop locked the memory spine, so memory writes are blocked until resume."
            status_code = 503
        elif status == "paused":
            summary = f"System Guard is paused, so {subject} are temporarily blocked."
            status_code = 423
        elif status == "hard_stopped":
            summary = f"System Guard is in hard stop, so {subject} remain frozen until resume."
            status_code = 503
        else:
            summary = f"System Guard is in safe stop, so {subject} stay blocked until resume."
            status_code = 503

        return {
            "allowed": False,
            "target": normalized_target,
            "summary": summary,
            "status_code": status_code,
            "guidance": [
                "Use Resume in the Jarvis System Guard panel when you want to re-enable new turns.",
            ],
            "system_guard": snapshot,
        }

    def _load_from_disk(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        if self._state_path.exists():
            try:
                payload = json.loads(self._state_path.read_text(encoding="utf-8"))
                self._state = SystemGuardState(
                    status=payload.get("status", "nominal"),
                    summary=payload.get("summary", SystemGuardState().summary),
                    reason=payload.get("reason", "system_started"),
                    last_action=payload.get("last_action", "resume"),
                    updated_at=payload.get("updated_at", _utc_now_iso()),
                    accepting_turns=bool(payload.get("accepting_turns", True)),
                    accepting_actions=bool(payload.get("accepting_actions", True)),
                    accepting_memory_writes=bool(payload.get("accepting_memory_writes", True)),
                    actor=payload.get("actor", "system"),
                    event_count=int(payload.get("event_count", 0)),
                )
            except Exception:
                self._state = SystemGuardState()

        if self._events_path.exists():
            loaded_events: list[dict] = []
            for line in self._events_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    loaded_events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            self._events = loaded_events[-80:]

    def _set_state(
        self,
        *,
        status: str,
        action: str,
        summary: str,
        reason: str,
        actor: str,
        accepting_turns: bool,
        accepting_actions: bool,
        accepting_memory_writes: bool,
    ) -> dict:
        with self._lock:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)

            event = {
                "id": str(uuid.uuid4()),
                "action": action,
                "status": status,
                "summary": summary,
                "reason": _clip_text(reason, limit=220),
                "actor": actor,
                "timestamp": _utc_now_iso(),
            }

            self._events.append(event)
            if len(self._events) > 80:
                del self._events[: len(self._events) - 80]

            self._state = SystemGuardState(
                status=status,
                summary=summary,
                reason=event["reason"],
                last_action=action,
                updated_at=event["timestamp"],
                accepting_turns=accepting_turns,
                accepting_actions=accepting_actions,
                accepting_memory_writes=accepting_memory_writes,
                actor=actor,
                event_count=len(self._events),
            )

            self._state_path.write_text(
                json.dumps(self._state.to_dict(), indent=2),
                encoding="utf-8",
            )
            with self._events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")

            payload = self._state.to_dict()
            payload["recent_events"] = [dict(item) for item in reversed(self._events[-6:])]
            return payload


system_guard = SystemGuardController()
