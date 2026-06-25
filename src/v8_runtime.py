"""V8-inspired session lifecycle, event log, and policy helpers for Jarvis."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import threading
import uuid


SESSION_STATES = {
    "idle",
    "primed",
    "gathering",
    "planning",
    "responding",
    "awaiting_approval",
    "acting",
    "ready",
    "degraded",
    "closed",
}

ALLOWED_TRANSITIONS = {
    "idle": {"primed", "gathering", "acting", "degraded", "closed"},
    "primed": {"gathering", "planning", "responding", "awaiting_approval", "acting", "ready", "degraded"},
    "gathering": {"planning", "responding", "awaiting_approval", "ready", "degraded"},
    "planning": {"responding", "awaiting_approval", "ready", "degraded"},
    "responding": {"ready", "awaiting_approval", "degraded"},
    "awaiting_approval": {"acting", "ready", "degraded"},
    "acting": {"ready", "degraded"},
    "ready": {"primed", "gathering", "planning", "responding", "awaiting_approval", "acting", "degraded", "closed"},
    "degraded": {"primed", "gathering", "planning", "ready", "closed"},
    "closed": set(),
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _clip_text(value, limit=600):
    text = " ".join(str(value or "").split()).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _sanitize_payload(payload, max_items=10):
    """Keep event payloads compact and JSON-safe for local storage."""
    if payload is None:
        return None
    if isinstance(payload, dict):
        result = {}
        for index, (key, value) in enumerate(payload.items()):
            if index >= max_items:
                break
            result[str(key)] = _sanitize_payload(value, max_items=max_items)
        return result
    if isinstance(payload, list):
        return [_sanitize_payload(item, max_items=max_items) for item in payload[:max_items]]
    if isinstance(payload, tuple):
        return [_sanitize_payload(item, max_items=max_items) for item in payload[:max_items]]
    if isinstance(payload, (str, int, float, bool)) or payload is None:
        if isinstance(payload, str):
            return _clip_text(payload, limit=1000)
        return payload
    return _clip_text(repr(payload), limit=1000)


def _default_runtime_dir():
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def default_policy_status():
    """Return a clean baseline policy posture for a new session."""
    return _wrap_ul_payload({
        "status": "allow",
        "allowed": True,
        "posture": "nominal",
        "summary": "No policy checks have been triggered yet.",
        "violations": [],
        "guidance": [],
        "checked_at": _utc_now_iso(),
        "target": "session",
    })


def derive_policy_posture(session) -> str:
    """Infer a compact posture from the live session state."""
    if session.session_state.state == "degraded":
        return "degraded"
    if session.spiral_state.uncertainty >= 0.80 or session.spiral_state.confidence <= 0.28:
        return "cautious"
    return "nominal"


@dataclass
class SessionLifecycle:
    """Track the live lifecycle state for one Jarvis session."""

    state: str = "idle"
    summary: str = "Session initialized."
    reason: str = "session_created"
    updated_at: str = field(default_factory=_utc_now_iso)
    transition_count: int = 0
    last_event_type: str = "session_created"

    def transition(self, next_state: str, summary: str, reason: str | None = None, event_type: str | None = None):
        normalized = str(next_state or "idle").strip().lower().replace(" ", "_")
        if normalized not in SESSION_STATES:
            normalized = "idle"

        current = self.state
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        forced = normalized != current and normalized not in allowed

        self.state = normalized
        self.summary = _clip_text(summary or self.summary, limit=180) or self.summary
        self.reason = _clip_text(reason or normalized, limit=120) or normalized
        self.updated_at = _utc_now_iso()
        self.transition_count += 1
        self.last_event_type = event_type or self.reason

        return {
            "from_state": current,
            "to_state": self.state,
            "summary": self.summary,
            "reason": self.reason,
            "updated_at": self.updated_at,
            "transition_count": self.transition_count,
            "forced": forced,
            "event_type": self.last_event_type,
        }

    def to_dict(self):
        return {
            "state": self.state,
            "summary": self.summary,
            "reason": self.reason,
            "updated_at": self.updated_at,
            "transition_count": self.transition_count,
            "last_event_type": self.last_event_type,
        }


class V8EventLog:
    """Small local-first event log with in-memory cache and JSONL persistence."""

    def __init__(self, runtime_dir: str | Path | None = None, max_events_per_session: int = 250):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir()) / "v8-events"
        self.max_events_per_session = max_events_per_session
        self._events: dict[str, list[dict]] = {}
        self._lock = threading.Lock()

    def _session_path(self, session_id: str) -> Path:
        return self.runtime_dir / f"{session_id}.jsonl"

    def append(self, session_id: str, event_type: str, state: str, summary: str, payload=None):
        event = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "event_type": str(event_type or "event").strip().lower().replace(" ", "_"),
            "state": str(state or "idle").strip().lower().replace(" ", "_"),
            "summary": _clip_text(summary, limit=220),
            "payload": _sanitize_payload(payload),
            "timestamp": _utc_now_iso(),
        }

        with self._lock:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            events = self._events.setdefault(session_id, [])
            events.append(event)
            if len(events) > self.max_events_per_session:
                del events[: len(events) - self.max_events_per_session]

            with self._session_path(session_id).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")

        return dict(event)

    def list_events(self, session_id: str, limit: int = 50):
        normalized_limit = max(1, min(int(limit or 50), self.max_events_per_session))
        with self._lock:
            if session_id not in self._events:
                path = self._session_path(session_id)
                loaded = []
                if path.exists():
                    for line in path.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            loaded.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                self._events[session_id] = loaded[-self.max_events_per_session :]

            events = self._events.get(session_id, [])
            return [dict(event) for event in events[-normalized_limit:]]


@dataclass
class PolicyDecision:
    """Compact response from the local policy engine."""

    allowed: bool
    status: str
    posture: str
    summary: str
    target: str
    violations: list[str] = field(default_factory=list)
    guidance: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self):
        return _wrap_ul_payload({
            "allowed": self.allowed,
            "status": self.status,
            "posture": self.posture,
            "summary": self.summary,
            "target": self.target,
            "violations": list(self.violations),
            "guidance": list(self.guidance),
            "checked_at": self.checked_at,
        })


class V8PolicyEngine:
    """Evaluate lightweight local policies for turns and safe operator actions."""

    def evaluate_turn(self, session, user_message: str, response_mode: str, use_research=None):
        lower = " ".join(str(user_message or "").lower().split())
        normalized_mode = str(response_mode or "fast").strip().lower().replace(" ", "_")
        posture = derive_policy_posture(session)
        violations = []
        guidance = []

        if posture == "cautious" and response_mode == "fast":
            guidance.append("Think mode may fit better while uncertainty is elevated.")

        if normalized_mode == "research" and use_research is False:
            guidance.append("Research mode is strongest when live research stays enabled.")

        if normalized_mode == "debug" and not any(
            token in lower for token in ("error", "traceback", "stack", "bug", "test", "route", "api", "log")
        ):
            guidance.append("Debug mode works best when you include the failing file, route, or error signal.")

        if normalized_mode == "operator" and any(
            token in lower for token in ("run", "check", "verify", "status", "build", "test")
        ):
            guidance.append("Operator mode can propose a safe local action when you want to verify this directly.")

        if use_research is False and any(token in lower for token in ("latest", "current", "recent", "news")):
            guidance.append("Live research is off for a freshness-sensitive request.")

        if len(lower) > 320 and response_mode == "fast":
            guidance.append("Fast mode may compress a long request too aggressively.")

        status = "warn" if guidance or violations else "allow"
        summary = (
            "Turn can proceed normally."
            if status == "allow"
            else "Turn can proceed, but Jarvis should stay aware of the active constraints."
        )
        return PolicyDecision(
            allowed=not violations,
            status="deny" if violations else status,
            posture=posture,
            summary=summary,
            target="turn",
            violations=violations,
            guidance=guidance,
        )

    def evaluate_action(self, session, action: dict | None, approved: bool):
        posture = derive_policy_posture(session)
        violations = []
        guidance = []

        if action is None:
            violations.append("Unknown action.")
        else:
            if action.get("requires_approval") and not approved:
                violations.append("Explicit approval is required before running local actions.")
            if posture == "cautious":
                guidance.append("Jarvis is in a cautious posture, so action output should be reviewed closely.")
            if session.metadata.get("response_mode") == "fast" and action.get("category") == "verification":
                guidance.append("Verification actions still work in Fast mode, but Think mode may give better follow-through.")

        allowed = not violations
        summary = (
            "Action is allowed under the current local policy."
            if allowed
            else "Action is blocked by the local policy guardrails."
        )
        return PolicyDecision(
            allowed=allowed,
            status="allow" if allowed and not guidance else ("warn" if allowed else "deny"),
            posture=posture,
            summary=summary,
            target="action",
            violations=violations,
            guidance=guidance,
        )


v8_event_log = V8EventLog()
v8_policy_engine = V8PolicyEngine()
