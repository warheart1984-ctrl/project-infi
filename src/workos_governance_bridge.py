"""Bridge AAIS operator governance to WorkOS RBAC permissions and Audit Logs.

Maps genome operator_lanes capabilities to WorkOS permission slugs and converts
operator decision ledger (ODL) events into WorkOS audit-log payloads. Optional
Flask guard for /api/operator/* routes when WorkOS AuthKit session is present.
"""

# Engineering: WorkOsGovernanceBridgeEngine

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

MODULE_ID = "AAIS-WOS-01"

# AAIS genome capabilities → WorkOS RBAC permission slugs (check permissions, not role slugs).
AAIS_CAPABILITY_TO_WORKOS_PERMISSION: dict[str, str] = {
    "approve_policy_changes": "governance.policy.approve",
    "observe_culture_of_beings_drift": "governance.drift.observe",
    "adopt_shared_norm": "governance.norm.adopt",
    "observe_multi_being_drift": "governance.drift.observe",
    "adopt_multi_being_pact": "governance.pact.adopt",
    "observe_social_drift": "governance.drift.observe",
    "adopt_social_bond": "governance.bond.adopt",
    "observe_autobiographical_drift": "governance.drift.observe",
    "adopt_autobiographical_episode": "governance.episode.adopt",
    "observe_narrative_drift": "governance.drift.observe",
    "adopt_narrative_beat": "governance.beat.adopt",
}

# Operator API routes → required WorkOS permission when bridge auth is enabled.
OPERATOR_ROUTE_PERMISSIONS: dict[str, str] = {
    "GET /api/operator/ledger": "governance.ledger.read",
    "GET /api/operator/ledger/digest": "governance.ledger.read",
    "GET /api/operator/ledger/query": "governance.ledger.read",
    "GET /api/operator/ledger/diff": "governance.ledger.read",
    "POST /api/operator/plugins/rescan": "governance.plugins.rescan",
}

_DECISION_TO_AUDIT_ACTION: dict[str, str] = {
    "allow": "allowed",
    "approve": "approved",
    "reject": "rejected",
    "block": "blocked",
    "pending": "pending",
    "completed": "completed",
    "failed": "failed",
    "defer": "deferred",
}

_KIND_TO_AUDIT_OBJECT: dict[str, str] = {
    "pipeline_turn": "pipeline_turn",
    "otem_approval": "approval",
    "urg_receipt": "urg_receipt",
    "checkpoint_block": "checkpoint",
    "plug_execution": "plugin_execution",
    "brain_decision": "brain_decision",
}


def workos_bridge_enabled() -> bool:
    raw = os.getenv("AAIS_WORKOS_BRIDGE", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def workos_audit_emit_enabled() -> bool:
    if not workos_bridge_enabled():
        return False
    raw = os.getenv("AAIS_WORKOS_AUDIT_EMIT", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def workos_api_configured() -> bool:
    return bool(os.getenv("WORKOS_API_KEY", "").strip())


def permission_for_aais_capability(capability: str) -> str | None:
    return AAIS_CAPABILITY_TO_WORKOS_PERMISSION.get(str(capability or "").strip())


def decision_event_to_audit_log(event: dict[str, Any]) -> dict[str, Any]:
    """Convert an ODL row into a WorkOS Audit Logs create-event payload."""
    kind = str(event.get("kind") or "decision").strip().lower()
    decision = str(event.get("decision") or "recorded").strip().lower()
    obj = _KIND_TO_AUDIT_OBJECT.get(kind, "decision")
    action = _DECISION_TO_AUDIT_ACTION.get(decision, "recorded")
    targets: list[dict[str, str]] = []
    if event.get("decision_id"):
        targets.append({"type": "decision", "id": str(event["decision_id"])[:40]})
    if event.get("session_id"):
        targets.append({"type": "session", "id": str(event["session_id"])[:40]})
    metadata: dict[str, str] = {
        "module_id": MODULE_ID,
        "kind": kind[:40],
        "decision": decision[:40],
        "claim_label": str(event.get("claim_label") or "asserted")[:40],
    }
    if event.get("summary"):
        metadata["summary"] = str(event["summary"])[:500]
    if event.get("jarvis_receipt_id"):
        metadata["jarvis_receipt_id"] = str(event["jarvis_receipt_id"])[:40]
    if event.get("tenant_id"):
        metadata["tenant_id"] = str(event["tenant_id"])[:40]
    actor: dict[str, str] = {"type": "user", "id": "system"}
    if event.get("operator_id"):
        actor = {"type": "user", "id": str(event["operator_id"])[:40]}
    return {
        "action": f"governance.{obj}.{action}",
        "occurred_at": str(event.get("recorded_at") or ""),
        "actor": actor,
        "targets": targets[:5],
        "metadata": metadata,
        "context": {
            "location": str(event.get("session_id") or "global")[:40],
        },
    }


def emit_workos_audit_event(
    event: dict[str, Any],
    *,
    organization_id: str | None = None,
) -> dict[str, Any]:
    """Emit a WorkOS audit log event when configured; otherwise no-op."""
    if not workos_audit_emit_enabled():
        return {"ok": False, "skipped": True, "reason": "bridge_or_emit_disabled"}
    if not workos_api_configured():
        return {"ok": False, "skipped": True, "reason": "workos_api_key_missing"}

    org_id = (organization_id or os.getenv("WORKOS_ORGANIZATION_ID") or "").strip()
    if not org_id:
        return {"ok": False, "skipped": True, "reason": "workos_organization_id_missing"}

    payload = decision_event_to_audit_log(event)
    try:
        from workos import WorkOSClient

        client = WorkOSClient(
            api_key=os.environ["WORKOS_API_KEY"],
            client_id=os.getenv("WORKOS_CLIENT_ID") or None,
        )
        client.audit_logs.create_event(organization_id=org_id, **payload)
        return {"ok": True, "skipped": False, "action": payload["action"]}
    except ImportError:
        return {"ok": False, "skipped": True, "reason": "workos_sdk_not_installed"}
    except Exception as exc:
        logger.warning("WorkOS audit emit failed: %s", exc)
        return {"ok": False, "skipped": False, "reason": str(exc)}


def maybe_emit_ledger_audit_event(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return emit_workos_audit_event(row)


def session_has_permission(session: dict[str, Any], permission: str) -> bool:
    """Check WorkOS RBAC permissions on an AuthKit session (not role slugs)."""
    perms = set(session.get("permissions") or [])
    if permission in perms:
        return True
    role = session.get("role") or {}
    role_perms = set(role.get("permissions") or [])
    return permission in role_perms


def require_workos_permission(permission: str) -> Callable:
    """Flask decorator: enforce a WorkOS permission when bridge auth is enabled."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any):
            if not workos_bridge_enabled():
                return view(*args, **kwargs)
            from flask import g, jsonify

            session = getattr(g, "workos_session", None)
            if not session:
                return jsonify({"error": "workos_session_required", "permission": permission}), 401
            if not session_has_permission(session, permission):
                return jsonify({"error": "workos_permission_denied", "permission": permission}), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator
