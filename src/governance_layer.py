"""Governance layer for policy promotion, overrides, and break-glass control."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import threading
from typing import Any
import uuid

from src.state_hygiene import (
    filter_operator_records,
    normalize_truth_scope,
    project_record,
    summarize_records,
)


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


GOVERNANCE_ROLES = {
    "owner": {
        "label": "Owner",
        "capabilities": [
            "approve_policy_changes",
            "override_crisis_mode",
            "authorize_break_glass",
            "promote_policies_to_production",
        ],
    },
    "security_engineer": {
        "label": "Security Engineer",
        "capabilities": [
            "edit_policies",
            "run_simulations",
            "publish_to_staging",
        ],
    },
    "observer": {
        "label": "Observer",
        "capabilities": [
            "view_events",
            "view_alerts",
            "view_dashboards",
        ],
    },
}


@dataclass
class BreakGlassState:
    active: bool = False
    approved_by: str | None = None
    approved_role: str | None = None
    scope: str | None = None
    duration_minutes: int | None = None
    reason: str | None = None
    activated_at: str | None = None
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "approved_by": self.approved_by,
            "approved_role": self.approved_role,
            "scope": self.scope,
            "duration_minutes": self.duration_minutes,
            "reason": self.reason,
            "activated_at": self.activated_at,
            "expires_at": self.expires_at,
        }


class GovernanceLayer:
    """Persist governance events, promotion requests, and break-glass state."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir()) / "governance"
        self._lock = threading.Lock()
        self._events: list[dict[str, Any]] = []
        self._policy_requests: list[dict[str, Any]] = []
        self._break_glass = BreakGlassState()
        self._load()

    @property
    def _events_path(self) -> Path:
        return self.runtime_dir / "governance-events.jsonl"

    @property
    def _requests_path(self) -> Path:
        return self.runtime_dir / "policy-requests.json"

    @property
    def _break_glass_path(self) -> Path:
        return self.runtime_dir / "break-glass.json"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            base_dir = Path(runtime_dir)
            self.runtime_dir = base_dir if base_dir.name == "governance" else base_dir / "governance"
            self._events = []
            self._policy_requests = []
            self._break_glass = BreakGlassState()
            self._load()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._events = []
            self._policy_requests = []
            self._break_glass = BreakGlassState()
            self._persist_locked()
        return self.snapshot(limit_events=0, limit_requests=0)

    def snapshot(self, limit_events: int = 10, limit_requests: int = 8) -> dict[str, Any]:
        return self.snapshot_with_scope(limit_events=limit_events, limit_requests=limit_requests, truth_scope="live")

    def _project_request(self, request: dict[str, Any]) -> dict[str, Any]:
        projected = project_record(dict(request or {}), kind="policy_request", source_type="governance_state")
        projected.pop("_state_hygiene_kind", None)
        return projected

    def _project_event(self, event: dict[str, Any]) -> dict[str, Any]:
        projected = project_record(dict(event or {}), kind="governance_event", source_type="governance_event")
        projected.pop("_state_hygiene_kind", None)
        return projected

    def snapshot_with_scope(
        self,
        *,
        limit_events: int = 10,
        limit_requests: int = 8,
        truth_scope: str = "live",
    ) -> dict[str, Any]:
        with self._lock:
            self._expire_break_glass_locked()
            scope = normalize_truth_scope(truth_scope)
            requests = [self._project_request(request) for request in self._policy_requests]
            events = [self._project_event(event) for event in self._events]
            if scope != "all":
                requests = filter_operator_records(requests, truth_scope=scope)
                events = filter_operator_records(events, truth_scope=scope)
            requests = requests[-max(0, int(limit_requests or 0)):]
            events = events[-max(0, int(limit_events or 0)):]
            break_glass = project_record(
                {
                    "id": "break_glass",
                    "status": "promoted" if self._break_glass.active else "draft",
                    **self._break_glass.to_dict(),
                },
                kind="policy_request",
                source_type="governance_state",
            )
            break_glass.pop("_state_hygiene_kind", None)
            from src.aais_ul.runtime import wrap_runtime_snapshot

            return wrap_runtime_snapshot(
                {
                    "roles": GOVERNANCE_ROLES,
                    "active_break_glass": break_glass,
                    "open_policy_requests": [
                        request for request in requests
                        if request.get("status") in {"draft", "staged", "blocked"}
                    ],
                    "recent_events": [dict(event) for event in events],
                    "request_count": len(self._policy_requests),
                    "event_count": len(self._events),
                    "truth_scope": scope,
                    "state_hygiene": {
                        "requests": summarize_records([self._project_request(item) for item in self._policy_requests]),
                        "events": summarize_records([self._project_event(item) for item in self._events]),
                    },
                }
            )

    def list_policy_requests(
        self,
        status: str | None = None,
        limit: int = 25,
        truth_scope: str = "live",
    ) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit or 25), 100))
        normalized_status = str(status or "").strip().lower() or None
        with self._lock:
            requests = [self._project_request(item) for item in self._policy_requests]
        if normalize_truth_scope(truth_scope) != "all":
            requests = filter_operator_records(requests, truth_scope=truth_scope)
        if normalized_status:
            requests = [request for request in requests if request.get("status") == normalized_status]
        return [dict(request) for request in requests[-normalized_limit:]]

    def get_policy_request(self, request_id: str) -> dict[str, Any] | None:
        with self._lock:
            return next((dict(item) for item in self._policy_requests if item.get("id") == request_id), None)

    def submit_policy_request(
        self,
        *,
        title: str,
        actor_id: str,
        actor_role: str,
        dsl_text: str = "",
        risk_score: float | None = None,
        changelog: str | None = None,
        diff_summary: str | None = None,
        shadow_divergence: bool | None = None,
        unit_tests_passed: bool | None = None,
        state_class: str | None = None,
        truth_status: str | None = None,
    ) -> dict[str, Any]:
        if actor_role not in {"owner", "security_engineer"}:
            raise PermissionError("Only owners and security engineers may submit policy requests.")
        request_id = f"pol_{uuid.uuid4().hex[:10]}"
        checks = {
            "dsl_valid": bool(str(dsl_text or "").strip()),
            "simulation_passed": True,
            "risk_score": float(risk_score if risk_score is not None else 2.5),
            "unit_tests_passed": True if unit_tests_passed is None else bool(unit_tests_passed),
            "shadow_divergence_clear": True if shadow_divergence is None else not bool(shadow_divergence),
        }
        checks["all_passed"] = (
            checks["dsl_valid"]
            and checks["simulation_passed"]
            and checks["unit_tests_passed"]
            and checks["shadow_divergence_clear"]
            and checks["risk_score"] <= 4.5
        )
        payload = {
            "id": request_id,
            "title": title.strip(),
            "status": "staged" if checks["all_passed"] else "blocked",
            "submitted_at": _utc_now_iso(),
            "submitted_by": actor_id,
            "submitted_role": actor_role,
            "dsl_text": dsl_text,
            "checks": checks,
            "changelog": changelog or "No changelog provided.",
            "diff_summary": diff_summary or "No diff summary provided.",
            "approval": None,
            "state_class": state_class,
            "truth_status": truth_status,
        }
        with self._lock:
            self._policy_requests.append(payload)
            self._policy_requests = self._policy_requests[-100:]
            self._append_event_locked(
                actor_id=actor_id,
                actor_role=actor_role,
                event_type="policy_request_created",
                target=request_id,
                details={"status": payload["status"], "risk_score": checks["risk_score"]},
                reason="Submitted a policy change request for staging review.",
            )
            self._persist_locked()
        return dict(payload)

    def promote_policy_request(
        self,
        request_id: str,
        *,
        actor_id: str,
        actor_role: str,
        rollout_strategy: str = "full",
    ) -> dict[str, Any]:
        if actor_role != "owner":
            raise PermissionError("Only owners may promote policy changes.")
        with self._lock:
            request = next((item for item in self._policy_requests if item.get("id") == request_id), None)
            if request is None:
                raise KeyError("Policy request not found.")
            if request.get("status") != "staged":
                raise ValueError("Only staged policy requests may be promoted.")
            request["status"] = "promoted"
            request["approval"] = {
                "approved_by": actor_id,
                "approved_role": actor_role,
                "approved_at": _utc_now_iso(),
                "rollout_strategy": rollout_strategy,
            }
            self._append_event_locked(
                actor_id=actor_id,
                actor_role=actor_role,
                event_type="policy_promoted",
                target=request_id,
                details={
                    "risk_score": request["checks"]["risk_score"],
                    "rollout_strategy": rollout_strategy,
                },
                reason="Approved policy promotion to production.",
            )
            self._persist_locked()
            return dict(request)

    def reject_policy_request(
        self,
        request_id: str,
        *,
        actor_id: str,
        actor_role: str,
        reason: str,
    ) -> dict[str, Any]:
        if actor_role not in {"owner", "security_engineer"}:
            raise PermissionError("Only owners and security engineers may reject policy requests.")
        with self._lock:
            request = next((item for item in self._policy_requests if item.get("id") == request_id), None)
            if request is None:
                raise KeyError("Policy request not found.")
            request["status"] = "rejected"
            request["approval"] = {
                "rejected_by": actor_id,
                "rejected_role": actor_role,
                "rejected_at": _utc_now_iso(),
                "reason": reason,
            }
            self._append_event_locked(
                actor_id=actor_id,
                actor_role=actor_role,
                event_type="policy_rejected",
                target=request_id,
                details={"status": "rejected"},
                reason=reason,
            )
            self._persist_locked()
            return dict(request)

    def activate_break_glass(
        self,
        *,
        actor_id: str,
        actor_role: str,
        scope: str,
        duration_minutes: int,
        reason: str,
    ) -> dict[str, Any]:
        if actor_role != "owner":
            raise PermissionError("Only owners may activate break-glass.")
        duration = max(1, min(int(duration_minutes or 10), 60))
        activated_at = _utc_now()
        expires_at = activated_at + timedelta(minutes=duration)
        with self._lock:
            self._break_glass = BreakGlassState(
                active=True,
                approved_by=actor_id,
                approved_role=actor_role,
                scope=scope,
                duration_minutes=duration,
                reason=reason,
                activated_at=activated_at.isoformat(),
                expires_at=expires_at.isoformat(),
            )
            self._append_event_locked(
                actor_id=actor_id,
                actor_role=actor_role,
                event_type="break_glass",
                target=scope,
                details={"duration_minutes": duration, "scope": scope},
                reason=reason,
            )
            self._persist_locked()
            return self._break_glass.to_dict()

    def clear_break_glass(self, *, actor_id: str, actor_role: str, reason: str) -> dict[str, Any]:
        if actor_role != "owner":
            raise PermissionError("Only owners may clear break-glass.")
        with self._lock:
            self._break_glass = BreakGlassState()
            self._append_event_locked(
                actor_id=actor_id,
                actor_role=actor_role,
                event_type="break_glass_cleared",
                target="break_glass",
                details={},
                reason=reason,
            )
            self._persist_locked()
            return self._break_glass.to_dict()

    def record_override(
        self,
        *,
        actor_id: str,
        actor_role: str,
        target: str,
        details: dict[str, Any] | None = None,
        reason: str,
        state_class: str | None = None,
        truth_status: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            event = self._append_event_locked(
                actor_id=actor_id,
                actor_role=actor_role,
                event_type="override",
                target=target,
                details={
                    **dict(details or {}),
                    "state_class": state_class,
                    "truth_status": truth_status,
                },
                reason=reason,
            )
            self._persist_locked()
            return dict(event)

    def record_module_event(
        self,
        *,
        actor_id: str,
        actor_role: str,
        module_id: str,
        decision: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            event = self._append_event_locked(
                actor_id=actor_id,
                actor_role=actor_role,
                event_type=str(decision or "module_event").strip().lower(),
                target=f"module:{module_id}",
                details=dict(details or {}),
                reason=reason,
            )
            self._persist_locked()
            return dict(event)

    def _load(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
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
        if self._requests_path.exists():
            try:
                self._policy_requests = json.loads(self._requests_path.read_text(encoding="utf-8"))
            except Exception:
                self._policy_requests = []
        if self._break_glass_path.exists():
            try:
                payload = json.loads(self._break_glass_path.read_text(encoding="utf-8"))
                self._break_glass = BreakGlassState(**payload)
            except Exception:
                self._break_glass = BreakGlassState()

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._requests_path.write_text(json.dumps(self._policy_requests, indent=2), encoding="utf-8")
        self._break_glass_path.write_text(json.dumps(self._break_glass.to_dict(), indent=2), encoding="utf-8")
        with self._events_path.open("w", encoding="utf-8") as handle:
            for event in self._events[-250:]:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")

    def _expire_break_glass_locked(self) -> None:
        if not self._break_glass.active or not self._break_glass.expires_at:
            return
        try:
            expires_at = datetime.fromisoformat(self._break_glass.expires_at)
        except ValueError:
            expires_at = _utc_now()
        if expires_at <= _utc_now():
            self._break_glass = BreakGlassState()
            self._append_event_locked(
                actor_id="system",
                actor_role="system",
                event_type="break_glass_expired",
                target="break_glass",
                details={},
                reason="Break-glass access expired automatically.",
            )
            self._persist_locked()

    def _append_event_locked(
        self,
        *,
        actor_id: str,
        actor_role: str,
        event_type: str,
        target: str,
        details: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        event = {
            "id": f"gov_{uuid.uuid4().hex[:12]}",
            "timestamp": _utc_now_iso(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "event_type": event_type,
            "target": target,
            "details": details,
            "reason": _clip_text(reason),
            "state_class": str((details or {}).get("state_class") or "").strip() or None,
            "truth_status": str((details or {}).get("truth_status") or "").strip() or None,
        }
        self._events.append(event)
        self._events = self._events[-250:]
        return event

    def compact_history(self) -> dict[str, Any]:
        """Prune non-live governance history while preserving live events and requests."""
        pruned_events = 0
        pruned_requests = 0
        with self._lock:
            projected_events = [self._project_event(event) for event in self._events]
            keep_events: list[dict[str, Any]] = []
            non_live_events: list[dict[str, Any]] = []
            for raw, projected in zip(self._events, projected_events):
                if projected.get("state_class") == "live":
                    keep_events.append(raw)
                else:
                    non_live_events.append(raw)
            keep_events.extend(non_live_events[-25:])
            pruned_events = max(0, len(self._events) - len(keep_events))
            self._events = keep_events[-250:]

            projected_requests = [self._project_request(request) for request in self._policy_requests]
            keep_requests: list[dict[str, Any]] = []
            non_live_requests: list[dict[str, Any]] = []
            for raw, projected in zip(self._policy_requests, projected_requests):
                if projected.get("state_class") == "live":
                    keep_requests.append(raw)
                else:
                    non_live_requests.append(raw)
            keep_requests.extend(non_live_requests[-25:])
            pruned_requests = max(0, len(self._policy_requests) - len(keep_requests))
            self._policy_requests = keep_requests[-100:]
            if pruned_events or pruned_requests:
                self._persist_locked()
        return {"pruned_events": pruned_events, "pruned_policy_requests": pruned_requests}


governance_layer = GovernanceLayer()
