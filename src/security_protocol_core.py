"""Unified security vocabulary and audit stream for AAIS.

This module turns the April 7 security/protocol spec into a local-first Python
implementation. It is intentionally bounded: one shared action/resource model,
one policy table, and one event stream that higher layers can consult.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
from enum import Enum
import json
import os
from pathlib import Path
import threading
from typing import Any
import uuid


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _clip_text(value: Any, limit: int = 240) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


ROLE_RANKS = {
    "any": 0,
    "observer": 1,
    "internal": 2,
    "operator": 3,
    "security_engineer": 4,
    "restricted": 5,
    "confidential": 6,
    "critical": 7,
    "sealed": 8,
    "core": 9,
    "owner": 10,
    "system": 10,
}


class Action(str, Enum):
    READ_MEMORY = "read_memory"
    WRITE_MEMORY = "write_memory"
    UPDATE_MEMORY = "update_memory"
    LOAD_INTO_BUFFER = "load_into_buffer"
    PIN_MEMORY = "pin_memory"
    EVICT_MEMORY = "evict_memory"
    USE_TOOL = "use_tool"
    INIT_TOOL = "init_tool"
    SHUTDOWN_TOOL = "shutdown_tool"
    CALL_API = "call_api"
    SEND_NETWORK_REQUEST = "send_network_request"
    EMIT_OUTPUT = "emit_output"
    EMIT_SENSITIVE_OUTPUT = "emit_sensitive_output"
    CHANGE_CONFIG = "change_config"
    CHANGE_MODE = "change_mode"
    LOAD_MODULE = "load_module"
    UNLOAD_MODULE = "unload_module"
    EXECUTE_COMMAND = "execute_command"
    SPAWN_PROCESS = "spawn_process"
    ACCESS_FILESYSTEM = "access_filesystem"


class ResourceType(str, Enum):
    MEMORY = "memory"
    TOOL = "tool"
    API = "api"
    OUTPUT_CHANNEL = "output_channel"
    CONFIG = "config"
    SYSTEM = "system"


class AccessDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ALLOW_TRANSFORMED = "allow_transformed"


@dataclass(slots=True)
class CallerContext:
    id: str
    role: str = "operator"
    capabilities: list[str] = field(default_factory=list)
    mode: str = "normal"
    tenant_id: str = "local"
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "mode": self.mode,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
        }


@dataclass(slots=True)
class ResourceMeta:
    id: str
    type: ResourceType
    category: str
    sensitivity: int = 1
    channel: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "category": self.category,
            "sensitivity": int(self.sensitivity),
            "channel": self.channel,
        }


@dataclass(slots=True)
class GlobalPolicy:
    min_role: str
    max_sensitivity: int
    summary_only: bool
    allowed: bool
    required_capabilities: tuple[str, ...] = ()


@dataclass(slots=True)
class SecurityDecision:
    allowed: bool
    decision: AccessDecision
    reason: str
    summary: str
    policy_rule: str
    transformed: bool = False
    checked_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "decision": self.decision.value,
            "reason": self.reason,
            "summary": self.summary,
            "policy_rule": self.policy_rule,
            "transformed": self.transformed,
            "checked_at": self.checked_at,
        }


def _role_rank(role: str | None) -> int:
    return ROLE_RANKS.get(str(role or "").strip().lower(), 0)


def get_global_policy(resource_type: ResourceType, action: Action) -> GlobalPolicy:
    """Return the baseline AAIS policy for one resource/action pair."""
    table: dict[tuple[ResourceType, Action], GlobalPolicy] = {
        (ResourceType.MEMORY, Action.READ_MEMORY): GlobalPolicy("operator", 11, False, True),
        (ResourceType.MEMORY, Action.WRITE_MEMORY): GlobalPolicy("restricted", 9, False, True),
        (ResourceType.MEMORY, Action.UPDATE_MEMORY): GlobalPolicy("restricted", 9, False, True),
        (ResourceType.MEMORY, Action.LOAD_INTO_BUFFER): GlobalPolicy("operator", 11, False, True),
        (ResourceType.MEMORY, Action.PIN_MEMORY): GlobalPolicy("restricted", 8, False, True),
        (ResourceType.MEMORY, Action.EVICT_MEMORY): GlobalPolicy("operator", 11, False, True),
        (ResourceType.TOOL, Action.USE_TOOL): GlobalPolicy("operator", 8, True, True),
        (ResourceType.TOOL, Action.INIT_TOOL): GlobalPolicy("security_engineer", 12, False, True),
        (ResourceType.TOOL, Action.SHUTDOWN_TOOL): GlobalPolicy("security_engineer", 12, False, True),
        (
            ResourceType.API,
            Action.CALL_API,
        ): GlobalPolicy("operator", 9, True, True, required_capabilities=("tool:network",)),
        (
            ResourceType.API,
            Action.SEND_NETWORK_REQUEST,
        ): GlobalPolicy("restricted", 8, True, True, required_capabilities=("tool:network",)),
        (ResourceType.OUTPUT_CHANNEL, Action.EMIT_OUTPUT): GlobalPolicy("any", 6, False, True),
        (
            ResourceType.OUTPUT_CHANNEL,
            Action.EMIT_SENSITIVE_OUTPUT,
        ): GlobalPolicy("confidential", 9, True, True),
        (ResourceType.CONFIG, Action.CHANGE_CONFIG): GlobalPolicy("critical", 12, False, True),
        (ResourceType.CONFIG, Action.CHANGE_MODE): GlobalPolicy("core", 12, False, True),
        (ResourceType.CONFIG, Action.LOAD_MODULE): GlobalPolicy("core", 12, False, True),
        (ResourceType.CONFIG, Action.UNLOAD_MODULE): GlobalPolicy("core", 12, False, True),
        (ResourceType.SYSTEM, Action.EXECUTE_COMMAND): GlobalPolicy("core", 12, False, False),
        (ResourceType.SYSTEM, Action.SPAWN_PROCESS): GlobalPolicy("core", 12, False, False),
        (ResourceType.SYSTEM, Action.ACCESS_FILESYSTEM): GlobalPolicy("critical", 10, False, True),
    }
    return table.get((resource_type, action), GlobalPolicy("core", 1, False, False))


class SecurityProtocolCore:
    """Local-first enforcement vocabulary plus a durable security event stream."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir()) / "security-protocol"
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._load_events()

    @property
    def _events_path(self) -> Path:
        return self.runtime_dir / "security-events.jsonl"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            self.runtime_dir = Path(runtime_dir) / "security-protocol"
            self._events = []
            self._load_events()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._events = []
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            self._events_path.write_text("", encoding="utf-8")
        return self.snapshot(limit_events=0)

    def _load_events(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if not self._events_path.exists():
            self._events = []
            return
        loaded: list[dict[str, Any]] = []
        for line in self._events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                loaded.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        self._events = loaded[-250:]

    def list_events(self, limit: int = 25, decision: str | None = None) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit or 25), 250))
        normalized_decision = str(decision or "").strip().lower() or None
        with self._lock:
            events = list(self._events)
        if normalized_decision:
            events = [event for event in events if event.get("decision") == normalized_decision]
        return [dict(event) for event in events[-normalized_limit:]]

    def snapshot(self, limit_events: int = 12) -> dict[str, Any]:
        with self._lock:
            events = list(self._events)
        counts = {
            "allow": 0,
            "deny": 0,
            "allow_transformed": 0,
        }
        for event in events:
            decision = event.get("decision")
            if decision in counts:
                counts[decision] += 1
        from src.aais_ul_substrate import wrap_runtime_snapshot

        return wrap_runtime_snapshot(
            {
                "summary": "Unified policy brain for memory, tools, APIs, outputs, configs, and system operations.",
                "event_count": len(events),
                "decision_counts": counts,
                "last_event_at": events[-1]["timestamp"] if events else None,
                "recent_events": [dict(event) for event in events[-max(0, int(limit_events or 0)):]],
            }
        )

    def check_action(
        self,
        caller: CallerContext,
        resource: ResourceMeta,
        action: Action,
        *,
        immune_snapshot: dict[str, Any] | None = None,
        break_glass: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> SecurityDecision:
        """Evaluate one action and log the result."""
        decision, anomaly_score, reason, rule = self._evaluate(
            caller,
            resource,
            action,
            immune_snapshot=immune_snapshot,
            break_glass=break_glass,
        )
        payload = self._append_event(
            caller,
            resource,
            action,
            decision,
            reason=reason,
            policy_rule=rule,
            anomaly_score=anomaly_score,
            details=details,
        )
        summary = self._build_summary(caller, resource, action, decision, reason)
        return SecurityDecision(
            allowed=decision != AccessDecision.DENY,
            decision=decision,
            reason=reason,
            summary=summary,
            policy_rule=rule,
            transformed=decision == AccessDecision.ALLOW_TRANSFORMED,
            checked_at=payload["timestamp"],
        )

    def _evaluate(
        self,
        caller: CallerContext,
        resource: ResourceMeta,
        action: Action,
        *,
        immune_snapshot: dict[str, Any] | None,
        break_glass: dict[str, Any] | None,
    ) -> tuple[AccessDecision, float, str, str]:
        policy = get_global_policy(resource.type, action)
        policy_rule = f"{resource.type.value}.{action.value}"
        caller_role_rank = _role_rank(caller.role)
        max_role_rank = _role_rank(policy.min_role)
        immune_snapshot = dict(immune_snapshot or {})
        active_break_glass = dict((break_glass or {}).get("active") or {})
        break_glass_active = bool(active_break_glass) and active_break_glass.get("active", True)
        immune_bypass = break_glass_active and caller.role in {"owner", "system"}

        if not policy.allowed:
            return AccessDecision.DENY, 0.92, "Action is forbidden by default.", policy_rule
        if caller_role_rank < max_role_rank:
            return AccessDecision.DENY, 0.88, "Caller role is below the required minimum.", policy_rule

        if policy.required_capabilities:
            missing = [cap for cap in policy.required_capabilities if cap not in set(caller.capabilities)]
            if missing:
                return AccessDecision.DENY, 0.84, f"Missing required capabilities: {', '.join(missing)}.", policy_rule

        if not immune_bypass:
            quarantined = {
                item.get("resource_id")
                for item in immune_snapshot.get("quarantined_resources", [])
                if item.get("resource_id")
            }
            disabled_tools = {
                item.get("tool_id")
                for item in immune_snapshot.get("disabled_tools", [])
                if item.get("tool_id")
            }
            caller_overrides = immune_snapshot.get("caller_overrides") or {}
            caller_override = caller_overrides.get(caller.id) or {}
            system_mode = str(immune_snapshot.get("system_mode") or "normal").strip().lower()

            if resource.id in quarantined and resource.type != ResourceType.OUTPUT_CHANNEL:
                return AccessDecision.DENY, 0.94, "Resource is quarantined by the immune layer.", f"{policy_rule}.quarantine"

            if resource.type == ResourceType.TOOL and resource.id in disabled_tools:
                return AccessDecision.DENY, 0.91, "Tool is disabled by the immune layer.", f"{policy_rule}.disabled_tool"

            override_max = caller_override.get("max_sensitivity")
            if override_max is not None and int(resource.sensitivity) > int(override_max):
                if policy.summary_only:
                    return (
                        AccessDecision.ALLOW_TRANSFORMED,
                        0.74,
                        "Caller override forced summary-only access at a lower sensitivity ceiling.",
                        f"{policy_rule}.caller_override",
                    )
                return (
                    AccessDecision.DENY,
                    0.81,
                    "Caller override lowered the allowed sensitivity ceiling.",
                    f"{policy_rule}.caller_override",
                )

            if caller_override.get("summary_only"):
                return (
                    AccessDecision.ALLOW_TRANSFORMED,
                    0.66,
                    "Caller override forced summary-only handling.",
                    f"{policy_rule}.summary_only",
                )

            if system_mode == "crisis":
                if resource.type in {ResourceType.TOOL, ResourceType.API, ResourceType.SYSTEM, ResourceType.CONFIG}:
                    return AccessDecision.DENY, 0.95, "System is in crisis mode and only safe read paths remain open.", f"{policy_rule}.crisis"
                if resource.sensitivity > 6:
                    return AccessDecision.ALLOW_TRANSFORMED, 0.79, "System is in crisis mode, so output is reduced to summary-safe form.", f"{policy_rule}.crisis"

            if system_mode == "restricted":
                if resource.type in {ResourceType.TOOL, ResourceType.API, ResourceType.SYSTEM} and resource.sensitivity > 6:
                    return AccessDecision.DENY, 0.82, "Restricted mode blocks higher-risk tool, API, and system access.", f"{policy_rule}.restricted"
                if resource.sensitivity > 6 and policy.summary_only:
                    return AccessDecision.ALLOW_TRANSFORMED, 0.61, "Restricted mode downgraded the access path to summary-only.", f"{policy_rule}.restricted"

        if int(resource.sensitivity) > int(policy.max_sensitivity):
            if policy.summary_only:
                return (
                    AccessDecision.ALLOW_TRANSFORMED,
                    0.58,
                    "Sensitivity exceeds the raw-access ceiling, so only transformed output is allowed.",
                    policy_rule,
                )
            return AccessDecision.DENY, 0.78, "Sensitivity exceeds the allowed ceiling.", policy_rule

        if policy.summary_only:
            return AccessDecision.ALLOW_TRANSFORMED, 0.33, "Policy requires transformed access for this surface.", policy_rule
        return AccessDecision.ALLOW, 0.08, "Action is allowed under the unified policy model.", policy_rule

    def _append_event(
        self,
        caller: CallerContext,
        resource: ResourceMeta,
        action: Action,
        decision: AccessDecision,
        *,
        reason: str,
        policy_rule: str,
        anomaly_score: float,
        details: dict[str, Any] | None,
    ) -> dict[str, Any]:
        event = {
            "id": f"sec_{uuid.uuid4().hex[:12]}",
            "timestamp": _utc_now_iso(),
            "caller_id": caller.id,
            "caller_role": caller.role,
            "caller_mode": caller.mode,
            "resource_id": resource.id,
            "resource_type": resource.type.value,
            "resource_category": resource.category,
            "resource_sensitivity": int(resource.sensitivity),
            "action": action.value,
            "decision": decision.value,
            "reason": reason,
            "policy_rule": policy_rule,
            "anomaly_score": round(float(anomaly_score), 2),
            "details": dict(details or {}),
        }
        with self._lock:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            self._events.append(event)
            self._events = self._events[-250:]
            with self._events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")
        return event

    def _build_summary(
        self,
        caller: CallerContext,
        resource: ResourceMeta,
        action: Action,
        decision: AccessDecision,
        reason: str,
    ) -> str:
        actor = _clip_text(caller.id, limit=40)
        target = f"{resource.type.value}:{resource.id}"
        if decision == AccessDecision.ALLOW:
            return f"{actor} may {action.value} on {target}."
        if decision == AccessDecision.ALLOW_TRANSFORMED:
            return f"{actor} may {action.value} on {target}, but only through guardrailed transformation. {reason}"
        return f"{actor} may not {action.value} on {target}. {reason}"


security_protocol_core = SecurityProtocolCore()
