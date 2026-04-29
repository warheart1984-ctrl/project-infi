"""Adaptive immune posture for Jarvis.

The immune system listens to security events, adjusts defensive posture, and
persists a compact audit trail of what changed and why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import threading
from typing import Any
import uuid


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _clip_text(value: Any, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


@dataclass
class ImmuneState:
    system_mode: str = "normal"
    changed_at: str = field(default_factory=_utc_now_iso)
    reason: str = "baseline"
    isolated_modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    quarantined_modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    blacklisted_modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    quarantined_resources: dict[str, dict[str, Any]] = field(default_factory=dict)
    disabled_tools: dict[str, dict[str, Any]] = field(default_factory=dict)
    caller_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_incident_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_mode": self.system_mode,
            "changed_at": self.changed_at,
            "reason": self.reason,
            "isolated_modules": list(self.isolated_modules.values()),
            "quarantined_modules": list(self.quarantined_modules.values()),
            "blacklisted_modules": list(self.blacklisted_modules.values()),
            "quarantined_resources": list(self.quarantined_resources.values()),
            "disabled_tools": list(self.disabled_tools.values()),
            "caller_overrides": dict(self.caller_overrides),
            "active_incident_id": self.active_incident_id,
        }


class ImmuneSystemController:
    """Persist immune posture, events, and incidents for the operator console."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir()) / "immune-system"
        self._lock = threading.Lock()
        self._state = ImmuneState()
        self._events: list[dict[str, Any]] = []
        self._incidents: list[dict[str, Any]] = []
        self._load()

    @property
    def _state_path(self) -> Path:
        return self.runtime_dir / "immune-state.json"

    @property
    def _events_path(self) -> Path:
        return self.runtime_dir / "immune-events.jsonl"

    @property
    def _incidents_path(self) -> Path:
        return self.runtime_dir / "immune-incidents.json"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            self.runtime_dir = Path(runtime_dir) / "immune-system"
            self._state = ImmuneState()
            self._events = []
            self._incidents = []
            self._load()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._state = ImmuneState()
            self._events = []
            self._incidents = []
            self._persist_locked()
        return self.snapshot(limit_events=0, limit_incidents=0)

    def snapshot(self, limit_events: int = 10, limit_incidents: int = 4) -> dict[str, Any]:
        with self._lock:
            state = self._state.to_dict()
            state["recent_events"] = [dict(event) for event in self._events[-max(0, int(limit_events or 0)):]]
            state["incidents"] = [dict(incident) for incident in self._incidents[-max(0, int(limit_incidents or 0)):]]
            state["event_count"] = len(self._events)
            state["incident_count"] = len(self._incidents)
            active_incident = None
            if self._state.active_incident_id:
                active_incident = next(
                    (incident for incident in reversed(self._incidents) if incident.get("incident_id") == self._state.active_incident_id),
                    None,
                )
            state["active_incident"] = dict(active_incident) if active_incident else None
            return state

    def list_events(self, limit: int = 25) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit or 25), 250))
        with self._lock:
            return [dict(event) for event in self._events[-normalized_limit:]]

    def list_incidents(self, limit: int = 10) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit or 10), 100))
        with self._lock:
            return [dict(incident) for incident in self._incidents[-normalized_limit:]]

    def observe_security_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Translate one security event into immune posture updates."""
        severity = self._severity_for_event(event)
        actions: list[dict[str, Any]] = []
        caller_id = str(event.get("caller_id") or "").strip()
        resource_id = str(event.get("resource_id") or "").strip()
        resource_type = str(event.get("resource_type") or "").strip()
        action_name = str(event.get("action") or "").strip()
        reason = _clip_text(event.get("reason") or event.get("decision") or "security signal")

        with self._lock:
            if severity in {"medium", "high", "critical"} and caller_id:
                actions.append(self._tighten_caller_locked(caller_id, severity=severity, reason=reason))

            if severity in {"high", "critical"} and resource_id and resource_type in {"memory", "api", "tool", "config"}:
                actions.append(self._quarantine_resource_locked(resource_id, severity=severity, reason=reason))

            if severity == "critical" and resource_type == "tool" and resource_id:
                actions.append(self._disable_tool_locked(resource_id, reason=reason))

            next_mode = self._recommended_mode_locked(severity)
            if next_mode != self._state.system_mode:
                actions.append(self._set_mode_locked(next_mode, reason=f"{severity} security signal"))
                if next_mode in {"restricted", "crisis"}:
                    actions.append(self._open_incident_locked(trigger=reason, mode=next_mode, event=event))

            immune_event = {
                "id": f"imm_{uuid.uuid4().hex[:12]}",
                "timestamp": _utc_now_iso(),
                "caller_id": caller_id or None,
                "resource_id": resource_id or None,
                "action": "observe_security_event",
                "severity": severity,
                "triggered_by_alert": event.get("decision"),
                "alert_severity": severity,
                "details": {
                    "security_event_id": event.get("id"),
                    "security_action": action_name,
                    "security_decision": event.get("decision"),
                    "applied_actions": [action.get("action") for action in actions if action],
                },
            }
            self._events.append(immune_event)
            self._events = self._events[-250:]
            self._persist_locked()
            return {
                "severity": severity,
                "applied_actions": [action for action in actions if action],
                "event": dict(immune_event),
                "state": self._state.to_dict(),
            }

    def observe_module_signal(
        self,
        *,
        module_id: str,
        signal_type: str,
        severity: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Translate one module-governance signal into immune posture updates."""
        normalized_severity = str(severity or "medium").strip().lower()
        if normalized_severity not in {"low", "medium", "high", "critical"}:
            normalized_severity = "medium"
        module_key = str(module_id or "").strip()
        signal_key = str(signal_type or "boundary_violation").strip().lower()
        applied_actions: list[dict[str, Any]] = []

        with self._lock:
            if normalized_severity in {"low", "medium", "high", "critical"} and module_key:
                applied_actions.append(
                    self._isolate_module_locked(
                        module_key,
                        severity=normalized_severity,
                        reason=reason,
                        signal_type=signal_key,
                    )
                )

            if normalized_severity in {"medium", "high", "critical"} and module_key:
                applied_actions.append(
                    self._quarantine_module_locked(
                        module_key,
                        severity=normalized_severity,
                        reason=reason,
                        signal_type=signal_key,
                    )
                )
                applied_actions.append(
                    self._quarantine_resource_locked(
                        module_key,
                        severity=normalized_severity,
                        reason=reason,
                    )
                )

            if normalized_severity in {"high", "critical"} and module_key:
                applied_actions.append(
                    self._blacklist_module_locked(
                        module_key,
                        severity=normalized_severity,
                        reason=reason,
                        signal_type=signal_key,
                    )
                )

            next_mode = self._recommended_module_mode_locked(normalized_severity)
            if next_mode != self._state.system_mode:
                applied_actions.append(self._set_mode_locked(next_mode, reason=f"{normalized_severity} module governance signal"))
                if next_mode in {"restricted", "crisis"}:
                    applied_actions.append(
                        self._open_incident_locked(
                            trigger=reason,
                            mode=next_mode,
                            event={"caller_id": f"module:{module_key}", "resource_id": module_key},
                        )
                    )

            immune_event = {
                "id": f"imm_{uuid.uuid4().hex[:12]}",
                "timestamp": _utc_now_iso(),
                "caller_id": f"module:{module_key}" if module_key else None,
                "resource_id": module_key or None,
                "action": "observe_module_signal",
                "severity": normalized_severity,
                "triggered_by_alert": signal_key,
                "alert_severity": normalized_severity,
                "details": {
                    "module_id": module_key,
                    "signal_type": signal_key,
                    "reason": reason,
                    "applied_actions": [action.get("action") for action in applied_actions if action],
                    "signal_details": dict(details or {}),
                },
            }
            self._events.append(immune_event)
            self._events = self._events[-250:]
            self._persist_locked()
            return {
                "severity": normalized_severity,
                "applied_actions": [action for action in applied_actions if action],
                "event": dict(immune_event),
                "state": self._state.to_dict(),
            }

    def observe_protocol_signal(
        self,
        *,
        component_id: str,
        signal_type: str,
        severity: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record one bounded protocol-boundary signal without default module quarantine."""
        normalized_severity = str(severity or "low").strip().lower()
        if normalized_severity not in {"low", "medium", "high", "critical"}:
            normalized_severity = "low"
        component_key = str(component_id or "").strip() or "unknown_component"
        signal_key = str(signal_type or "protocol_anomaly").strip().lower() or "protocol_anomaly"
        signal_details = dict(details or {})
        source_id = str(
            signal_details.get("source")
            or signal_details.get("source_id")
            or signal_details.get("caller_id")
            or ""
        ).strip()
        caller_id = f"reasoning_exchange:{source_id}" if source_id else None
        applied_actions: list[dict[str, Any]] = []

        with self._lock:
            if normalized_severity in {"medium", "high", "critical"} and caller_id:
                applied_actions.append(
                    self._tighten_caller_locked(
                        caller_id,
                        severity=normalized_severity,
                        reason=reason,
                    )
                )

            if normalized_severity == "critical":
                applied_actions.append(
                    self._quarantine_resource_locked(
                        component_key,
                        severity=normalized_severity,
                        reason=reason,
                    )
                )

            next_mode = self._recommended_protocol_mode_locked(normalized_severity)
            if next_mode != self._state.system_mode:
                applied_actions.append(
                    self._set_mode_locked(
                        next_mode,
                        reason=f"{normalized_severity} protocol boundary signal",
                    )
                )
                if next_mode in {"restricted", "crisis"}:
                    applied_actions.append(
                        self._open_incident_locked(
                            trigger=reason,
                            mode=next_mode,
                            event={"caller_id": caller_id, "resource_id": component_key},
                        )
                    )

            immune_event = {
                "id": f"imm_{uuid.uuid4().hex[:12]}",
                "timestamp": _utc_now_iso(),
                "caller_id": caller_id,
                "resource_id": component_key,
                "action": "observe_protocol_signal",
                "severity": normalized_severity,
                "triggered_by_alert": signal_key,
                "alert_severity": normalized_severity,
                "details": {
                    "component_id": component_key,
                    "signal_type": signal_key,
                    "reason": reason,
                    "applied_actions": [action.get("action") for action in applied_actions if action],
                    "signal_details": signal_details,
                },
            }
            self._events.append(immune_event)
            self._events = self._events[-250:]
            self._persist_locked()
            return {
                "severity": normalized_severity,
                "applied_actions": [action for action in applied_actions if action],
                "event": dict(immune_event),
                "state": self._state.to_dict(),
            }

    def release_module(self, module_id: str, *, reason: str) -> dict[str, Any]:
        """Release a previously isolated or quarantined module after correction."""
        module_key = str(module_id or "").strip()
        with self._lock:
            isolated = self._state.isolated_modules.pop(module_key, None)
            quarantined = self._state.quarantined_modules.pop(module_key, None)
            self._state.quarantined_resources.pop(module_key, None)
            if not isolated and not quarantined:
                return {
                    "released": False,
                    "state": self._state.to_dict(),
                }
            event = {
                "id": f"imm_{uuid.uuid4().hex[:12]}",
                "timestamp": _utc_now_iso(),
                "caller_id": f"module:{module_key}",
                "resource_id": module_key,
                "action": "release_module",
                "severity": "low",
                "triggered_by_alert": "module_release",
                "alert_severity": "low",
                "details": {
                    "module_id": module_key,
                    "reason": reason,
                    "released_isolation": bool(isolated),
                    "released_quarantine": bool(quarantined),
                },
            }
            self._events.append(event)
            self._events = self._events[-250:]
            self._persist_locked()
            return {
                "released": True,
                "event": dict(event),
                "state": self._state.to_dict(),
            }

    def _severity_for_event(self, event: dict[str, Any]) -> str:
        decision = str(event.get("decision") or "allow").strip().lower()
        sensitivity = int(event.get("resource_sensitivity") or 1)
        action_name = str(event.get("action") or "").strip().lower()
        if decision == "deny" and (sensitivity >= 9 or action_name in {"change_config", "change_mode"}):
            return "critical"
        if decision == "deny" and sensitivity >= 7:
            return "high"
        if decision == "allow_transformed" and sensitivity >= 7:
            return "high"
        if decision == "deny" or decision == "allow_transformed":
            return "medium"
        return "low"

    def _recommended_mode_locked(self, severity: str) -> str:
        if severity == "critical":
            return "crisis"
        if severity == "high":
            return "restricted"
        if self._state.system_mode == "crisis":
            return "crisis"
        return self._state.system_mode

    def _recommended_module_mode_locked(self, severity: str) -> str:
        if severity == "critical":
            return "crisis"
        if severity in {"medium", "high"}:
            return "restricted"
        if self._state.system_mode == "crisis":
            return "crisis"
        return self._state.system_mode

    def _recommended_protocol_mode_locked(self, severity: str) -> str:
        if severity == "critical":
            return "crisis"
        if severity == "high":
            return "restricted"
        if self._state.system_mode == "crisis":
            return "crisis"
        return self._state.system_mode

    def _tighten_caller_locked(self, caller_id: str, *, severity: str, reason: str) -> dict[str, Any]:
        current = dict(self._state.caller_overrides.get(caller_id) or {})
        if severity == "critical":
            current.update({
                "rate_multiplier": 0.25,
                "max_sensitivity": 6,
                "summary_only": True,
            })
        elif severity == "high":
            current.update({
                "rate_multiplier": 0.5,
                "max_sensitivity": 8,
                "summary_only": True,
            })
        else:
            current.update({
                "rate_multiplier": min(float(current.get("rate_multiplier", 1.0)), 0.75),
                "max_sensitivity": min(int(current.get("max_sensitivity", 9)), 9),
                "summary_only": bool(current.get("summary_only", False)),
            })
        current["applied_at"] = _utc_now_iso()
        current["reason"] = reason
        self._state.caller_overrides[caller_id] = current
        return {
            "action": "tighten_caller",
            "caller_id": caller_id,
            "overrides": dict(current),
        }

    def _quarantine_resource_locked(self, resource_id: str, *, severity: str, reason: str) -> dict[str, Any]:
        payload = {
            "resource_id": resource_id,
            "quarantined_at": _utc_now_iso(),
            "severity": severity,
            "reason": reason,
        }
        self._state.quarantined_resources[resource_id] = payload
        return {
            "action": "quarantine_resource",
            **payload,
        }

    def _disable_tool_locked(self, tool_id: str, *, reason: str) -> dict[str, Any]:
        payload = {
            "tool_id": tool_id,
            "disabled_at": _utc_now_iso(),
            "reason": reason,
        }
        self._state.disabled_tools[tool_id] = payload
        return {
            "action": "disable_tool",
            **payload,
        }

    def _isolate_module_locked(
        self,
        module_id: str,
        *,
        severity: str,
        reason: str,
        signal_type: str,
    ) -> dict[str, Any]:
        payload = {
            "module_id": module_id,
            "isolated_at": _utc_now_iso(),
            "severity": severity,
            "signal_type": signal_type,
            "reason": reason,
        }
        self._state.isolated_modules[module_id] = payload
        return {
            "action": "isolate_module",
            **payload,
        }

    def _quarantine_module_locked(
        self,
        module_id: str,
        *,
        severity: str,
        reason: str,
        signal_type: str,
    ) -> dict[str, Any]:
        payload = {
            "module_id": module_id,
            "quarantined_at": _utc_now_iso(),
            "severity": severity,
            "signal_type": signal_type,
            "reason": reason,
        }
        self._state.quarantined_modules[module_id] = payload
        return {
            "action": "quarantine_module",
            **payload,
        }

    def _blacklist_module_locked(
        self,
        module_id: str,
        *,
        severity: str,
        reason: str,
        signal_type: str,
    ) -> dict[str, Any]:
        payload = {
            "module_id": module_id,
            "blacklisted_at": _utc_now_iso(),
            "severity": severity,
            "signal_type": signal_type,
            "reason": reason,
        }
        self._state.blacklisted_modules[module_id] = payload
        return {
            "action": "blacklist_module",
            **payload,
        }

    def _set_mode_locked(self, mode: str, *, reason: str) -> dict[str, Any]:
        self._state.system_mode = mode
        self._state.changed_at = _utc_now_iso()
        self._state.reason = reason
        return {
            "action": f"enter_{mode}_mode" if mode != "normal" else "return_to_normal_mode",
            "mode": mode,
            "reason": reason,
            "changed_at": self._state.changed_at,
        }

    def _open_incident_locked(self, *, trigger: str, mode: str, event: dict[str, Any]) -> dict[str, Any]:
        incident = {
            "incident_id": f"inc_{_utc_now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            "started_at": _utc_now_iso(),
            "trigger": trigger,
            "mode": mode,
            "affected_callers": [event.get("caller_id")] if event.get("caller_id") else [],
            "affected_resources": [event.get("resource_id")] if event.get("resource_id") else [],
            "summary": f"{mode.title()} mode entered after {trigger}.",
            "status": "open",
        }
        self._incidents.append(incident)
        self._incidents = self._incidents[-100:]
        self._state.active_incident_id = incident["incident_id"]
        return {
            "action": "open_incident",
            "incident_id": incident["incident_id"],
            "mode": mode,
        }

    def _load(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if self._state_path.exists():
            try:
                payload = json.loads(self._state_path.read_text(encoding="utf-8"))
                self._state = ImmuneState(
                    system_mode=payload.get("system_mode", "normal"),
                    changed_at=payload.get("changed_at", _utc_now_iso()),
                    reason=payload.get("reason", "baseline"),
                    isolated_modules={
                        item["module_id"]: item
                        for item in payload.get("isolated_modules", [])
                        if item.get("module_id")
                    },
                    quarantined_modules={
                        item["module_id"]: item
                        for item in payload.get("quarantined_modules", [])
                        if item.get("module_id")
                    },
                    blacklisted_modules={
                        item["module_id"]: item
                        for item in payload.get("blacklisted_modules", [])
                        if item.get("module_id")
                    },
                    quarantined_resources={
                        item["resource_id"]: item
                        for item in payload.get("quarantined_resources", [])
                        if item.get("resource_id")
                    },
                    disabled_tools={
                        item["tool_id"]: item
                        for item in payload.get("disabled_tools", [])
                        if item.get("tool_id")
                    },
                    caller_overrides=dict(payload.get("caller_overrides") or {}),
                    active_incident_id=payload.get("active_incident_id"),
                )
            except Exception:
                self._state = ImmuneState()

        if self._events_path.exists():
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

        if self._incidents_path.exists():
            try:
                self._incidents = json.loads(self._incidents_path.read_text(encoding="utf-8"))
            except Exception:
                self._incidents = []

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps(self._state.to_dict(), indent=2), encoding="utf-8")
        self._incidents_path.write_text(json.dumps(self._incidents, indent=2), encoding="utf-8")
        with self._events_path.open("w", encoding="utf-8") as handle:
            for event in self._events[-250:]:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")


immune_system = ImmuneSystemController()
