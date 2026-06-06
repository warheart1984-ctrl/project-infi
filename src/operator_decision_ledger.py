"""Operator Decision Ledger — cross-plane accountability action graph."""

# Mythic: Operator Decision Ledger
# Engineering: OperatorDecisionLedgerEngine
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.temporal_replay.paths import default_runtime_dir, operator_ledger_path

MODULE_ID = "AAIS-ODL-01"


class OperatorDecisionCheckpointError(RuntimeError):
    """Raised when checkpoint policy blocks irreversible execution."""

    def __init__(self, message: str, *, decision_id: str | None = None, action: str = "block"):
        super().__init__(message)
        self.decision_id = decision_id
        self.action = action


EVENT_VERSION = "operator_decision_event.v1"
LEDGER_VERSION = "operator_decision_ledger.v1"
MAX_GRAPH_NODES = 64
DEFAULT_LIST_LIMIT = 200

_DECISION_KINDS = frozenset(
    {
        "pipeline_turn",
        "otem_approval",
        "urg_receipt",
        "checkpoint_block",
        "plug_execution",
        "brain_decision",
    }
)
_DECISIONS = frozenset({"allow", "pending", "approve", "reject", "completed", "failed", "block", "defer"})
_REVERSIBILITY = frozenset({"undo_available", "cannot_undo", "not_applicable"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _clip_text(value: Any, limit: int) -> str:
    return str(value or "")[:limit]


def ledger_enabled() -> bool:
    raw = os.getenv("AAIS_OPERATOR_LEDGER_PERSIST", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def checkpoint_policy_enabled() -> bool:
    raw = os.getenv("AAIS_OPERATOR_LEDGER_CHECKPOINT", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _normalize_scope_id(scope_id: str | None) -> str:
    sid = str(scope_id or "").strip()
    return sid or "global"


def _new_decision_id() -> str:
    return f"odl_{uuid4().hex}"


def _bounded_blast_radius(raw: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(raw or {})
    files = [str(p)[:240] for p in list(source.get("affected_files") or [])[:12]]
    seams = []
    for item in list(source.get("integration_seams") or [])[:8]:
        if not isinstance(item, dict):
            continue
        seams.append(
            {
                "path": _clip_text(item.get("path"), 240),
                "kind": _clip_text(item.get("kind"), 64),
            }
        )
    risk = str(source.get("risk_level") or "low").strip().lower()
    if risk not in {"low", "medium", "high"}:
        risk = "low"
    result: dict[str, Any] = {"affected_files": files, "risk_level": risk}
    if source.get("impact_id"):
        result["impact_id"] = _clip_text(source.get("impact_id"), 64)
    if seams:
        result["integration_seams"] = seams
    return result


def _bounded_drift_context(raw: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(raw or {})
    band = str(source.get("drift_band") or "idle").strip().lower()
    if band not in {"nominal", "watch", "drifting", "critical", "idle"}:
        band = "idle"
    result: dict[str, Any] = {"drift_band": band}
    if source.get("trajectory_status"):
        result["trajectory_status"] = _clip_text(source.get("trajectory_status"), 32)
    if source.get("identity_distance") is not None:
        try:
            result["identity_distance"] = float(source.get("identity_distance"))
        except (TypeError, ValueError):
            pass
    if source.get("pipeline_id"):
        result["pipeline_id"] = _clip_text(source.get("pipeline_id"), 128)
    return result


def _bounded_federation(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    if not raw:
        return None
    source = dict(raw)
    digest = str(source.get("federation_digest") or "").strip()
    if not digest:
        return None
    result: dict[str, Any] = {"federation_digest": digest[:128]}
    if source.get("grant_id"):
        result["grant_id"] = _clip_text(source.get("grant_id"), 128)
    counterparty = dict(source.get("counterparty_receipt_ref") or {})
    if counterparty:
        result["counterparty_receipt_ref"] = {
            "tenant_id": _clip_text(counterparty.get("tenant_id"), 128),
            "mission_id": _clip_text(counterparty.get("mission_id"), 128),
            "grant_id": _clip_text(counterparty.get("grant_id"), 128),
        }
    return result


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    row = dict(event)
    row["event_version"] = EVENT_VERSION
    row.setdefault("decision_id", _new_decision_id())
    row.setdefault("recorded_at", _utc_now_iso())
    row.setdefault("causal_parents", [])
    row.setdefault("claim_label", "asserted")
    row.setdefault("cisiv_stage", "implementation")
    row["summary"] = _clip_text(row.get("summary"), 500)
    row["blast_radius"] = _bounded_blast_radius(row.get("blast_radius"))
    row["drift_context"] = _bounded_drift_context(row.get("drift_context"))
    federation = _bounded_federation(row.get("federation"))
    if federation:
        row["federation"] = federation
    else:
        row.pop("federation", None)
    for key in ("session_id", "pipeline_id", "approval_id", "mission_id", "tenant_id"):
        if row.get(key) is not None:
            row[key] = _clip_text(row.get(key), 128) or None
    parents = [str(p) for p in list(row.get("causal_parents") or [])[:8] if str(p).strip()]
    row["causal_parents"] = parents
    return row


class OperatorDecisionLedgerStore:
    """Thread-safe append-only JSONL store with hash chain."""

    def __init__(self, *, runtime_dir: Path | None = None):
        self._runtime_dir_override = runtime_dir
        self._lock = threading.Lock()
        self._index_lock = threading.Lock()
        self._last_by_session: dict[str, str] = {}
        self._last_by_pipeline: dict[str, str] = {}
        self._last_by_approval: dict[str, str] = {}
        self._last_by_mission: dict[str, str] = {}
        self._pending_by_approval: dict[str, str] = {}

    @property
    def runtime_dir(self) -> Path:
        return self._runtime_dir_override or default_runtime_dir()

    def configure_runtime_dir(self, runtime_dir: Path | str | None) -> None:
        self._runtime_dir_override = Path(runtime_dir) if runtime_dir else None
        with self._index_lock:
            self._last_by_session.clear()
            self._last_by_pipeline.clear()
            self._last_by_approval.clear()
            self._last_by_mission.clear()
            self._pending_by_approval.clear()

    def _events_path(self, scope_id: str) -> Path:
        return operator_ledger_path(scope_id, runtime_dir=self.runtime_dir)

    def _read_rows(self, scope_id: str) -> list[dict[str, Any]]:
        path = self._events_path(scope_id)
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def _rebuild_indexes(self, scope_id: str) -> None:
        rows = self._read_rows(scope_id)
        with self._index_lock:
            self._last_by_session.pop(scope_id, None)
            self._last_by_pipeline.clear()
            self._last_by_approval.clear()
            self._last_by_mission.clear()
            self._pending_by_approval.clear()
            last_id: str | None = None
            for row in rows:
                did = str(row.get("decision_id") or "")
                if not did:
                    continue
                last_id = did
                pipeline_id = row.get("pipeline_id")
                if pipeline_id:
                    self._last_by_pipeline[str(pipeline_id)] = did
                approval_id = row.get("approval_id")
                if approval_id:
                    self._last_by_approval[str(approval_id)] = did
                    if row.get("decision") == "pending":
                        self._pending_by_approval[str(approval_id)] = did
                mission_id = row.get("mission_id")
                if mission_id:
                    self._last_by_mission[str(mission_id)] = did
            if last_id:
                self._last_by_session[scope_id] = last_id

    def _ensure_indexes(self, scope_id: str) -> None:
        if scope_id not in self._last_by_session:
            self._rebuild_indexes(scope_id)

    def append(self, scope_id: str, event: dict[str, Any]) -> dict[str, Any] | None:
        if not ledger_enabled():
            return None
        scope = _normalize_scope_id(scope_id)
        row = _normalize_event(event)
        path = self._events_path(scope)
        with self._lock:
            prev_hash = ""
            if path.exists():
                rows = self._read_rows(scope)
                if rows:
                    prev_hash = str(rows[-1].get("row_hash") or "")
            body = {k: v for k, v in row.items() if k not in {"row_hash", "prev_row_hash"}}
            row_hash = sha256(_stable_json(body).encode("utf-8")).hexdigest()
            row["prev_row_hash"] = prev_hash
            row["row_hash"] = row_hash
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(_stable_json(row) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        with self._index_lock:
            did = str(row["decision_id"])
            self._last_by_session[scope] = did
            if row.get("pipeline_id"):
                self._last_by_pipeline[str(row["pipeline_id"])] = did
            if row.get("approval_id"):
                self._last_by_approval[str(row["approval_id"])] = did
                if row.get("decision") == "pending":
                    self._pending_by_approval[str(row["approval_id"])] = did
                elif str(row["approval_id"]) in self._pending_by_approval:
                    self._pending_by_approval.pop(str(row["approval_id"]), None)
            if row.get("mission_id"):
                self._last_by_mission[str(row["mission_id"])] = did
        try:
            from src.operator_decision_ledger_index import operator_decision_ledger_index

            operator_decision_ledger_index.append_index_entry(scope, row)
        except Exception:
            pass
        return row

    def list_events(
        self,
        scope_id: str,
        *,
        since: str | None = None,
        limit: int = DEFAULT_LIST_LIMIT,
        decision_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._read_rows(_normalize_scope_id(scope_id))
        if since:
            rows = [r for r in rows if str(r.get("recorded_at") or "") >= since]
        if decision_filter:
            rows = [r for r in rows if str(r.get("decision") or "") == decision_filter]
        cap = max(1, min(int(limit or DEFAULT_LIST_LIMIT), 500))
        return rows[-cap:]

    def get_event(self, scope_id: str, decision_id: str) -> dict[str, Any] | None:
        for row in self._read_rows(_normalize_scope_id(scope_id)):
            if str(row.get("decision_id")) == decision_id:
                return row
        return None

    def find_by_pipeline(self, scope_id: str, pipeline_id: str) -> str | None:
        self._ensure_indexes(_normalize_scope_id(scope_id))
        return self._last_by_pipeline.get(str(pipeline_id))

    def find_pending_by_approval(self, scope_id: str, approval_id: str) -> str | None:
        self._ensure_indexes(_normalize_scope_id(scope_id))
        return self._pending_by_approval.get(str(approval_id))

    def find_by_mission(self, scope_id: str, mission_id: str) -> str | None:
        self._ensure_indexes(_normalize_scope_id(scope_id))
        return self._last_by_mission.get(str(mission_id))

    def last_decision_id(self, scope_id: str) -> str | None:
        self._ensure_indexes(_normalize_scope_id(scope_id))
        return self._last_by_session.get(_normalize_scope_id(scope_id))

    def build_action_graph(self, scope_id: str, root_id: str) -> dict[str, Any]:
        scope = _normalize_scope_id(scope_id)
        rows = self._read_rows(scope)
        by_id = {str(r.get("decision_id")): r for r in rows if r.get("decision_id")}
        if root_id not in by_id:
            return {"root_id": root_id, "nodes": [], "edges": [], "truncated": False}
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, str]] = []
        seen: set[str] = set()
        queue = [root_id]
        truncated = False
        while queue and len(seen) < MAX_GRAPH_NODES:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            row = by_id.get(current)
            if not row:
                continue
            nodes.append(
                {
                    "decision_id": current,
                    "decision_kind": row.get("decision_kind"),
                    "decision": row.get("decision"),
                    "summary": row.get("summary"),
                    "recorded_at": row.get("recorded_at"),
                    "reversibility": row.get("reversibility"),
                }
            )
            for parent in list(row.get("causal_parents") or []):
                parent_id = str(parent)
                edges.append({"from": parent_id, "to": current})
                if parent_id not in seen:
                    queue.append(parent_id)
            for other_id, other in by_id.items():
                if other_id in seen:
                    continue
                if current in [str(p) for p in list(other.get("causal_parents") or [])]:
                    edges.append({"from": current, "to": other_id})
                    queue.append(other_id)
        if len(seen) >= MAX_GRAPH_NODES and queue:
            truncated = True
        return {
            "root_id": root_id,
            "scope_id": scope,
            "nodes": nodes,
            "edges": edges,
            "truncated": truncated,
            "node_count": len(nodes),
        }

    def compute_digest(self, scope_id: str) -> dict[str, Any]:
        rows = self._read_rows(_normalize_scope_id(scope_id))
        if not rows:
            return {"scope_id": _normalize_scope_id(scope_id), "entry_count": 0, "chain_root": ""}
        return {
            "scope_id": _normalize_scope_id(scope_id),
            "entry_count": len(rows),
            "chain_root": str(rows[0].get("row_hash") or ""),
            "chain_tip": str(rows[-1].get("row_hash") or ""),
            "latest_decision_id": str(rows[-1].get("decision_id") or ""),
        }

    def verify_chain(self, scope_id: str) -> dict[str, Any]:
        rows = self._read_rows(_normalize_scope_id(scope_id))
        prev = ""
        errors: list[str] = []
        for index, row in enumerate(rows):
            body = {k: v for k, v in row.items() if k not in {"row_hash", "prev_row_hash"}}
            expected = sha256(_stable_json(body).encode("utf-8")).hexdigest()
            row_hash = str(row.get("row_hash") or "")
            prev_row_hash = str(row.get("prev_row_hash") or "")
            if row_hash != expected:
                errors.append(f"row {index}: hash mismatch")
            if prev_row_hash != prev:
                errors.append(f"row {index}: prev_row_hash mismatch")
            prev = row_hash
        return {
            "scope_id": _normalize_scope_id(scope_id),
            "valid": not errors,
            "entry_count": len(rows),
            "errors": errors[:12],
        }

    def build_digest_summary(self, scope_id: str) -> dict[str, Any]:
        rows = self._read_rows(_normalize_scope_id(scope_id))
        pending = 0
        cannot_undo = 0
        cross_tenant = 0
        needs_review = 0
        latest_drift = "idle"
        for row in rows:
            if row.get("decision") == "pending":
                pending += 1
            if row.get("reversibility") == "cannot_undo":
                cannot_undo += 1
            if row.get("federation"):
                cross_tenant += 1
            if row.get("decision_kind") == "checkpoint_block":
                needs_review += 1
            drift = dict(row.get("drift_context") or {})
            if drift.get("drift_band"):
                latest_drift = str(drift.get("drift_band"))
        return {
            "scope_id": _normalize_scope_id(scope_id),
            "entry_count": len(rows),
            "pending_count": pending,
            "cannot_undo_count": cannot_undo,
            "cross_tenant_decisions_count": cross_tenant,
            "needs_review_count": needs_review,
            "latest_drift_band": latest_drift,
            "latest_decision_id": str(rows[-1].get("decision_id") or "") if rows else None,
        }


operator_decision_ledger_store = OperatorDecisionLedgerStore()


def _drift_context_from_pipeline(governed_pipeline: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(governed_pipeline, dict):
        return {"drift_band": "idle"}
    witness = dict(governed_pipeline.get("continuity_witness") or {})
    trajectory = str(witness.get("trajectory_status") or "STABLE")
    mapping = {
        "STABLE": "nominal",
        "WATCH": "watch",
        "DRIFTING": "drifting",
        "CRITICAL": "critical",
    }
    return {
        "drift_band": mapping.get(trajectory.upper(), "idle"),
        "trajectory_status": trajectory[:32],
        "identity_distance": witness.get("identity_distance"),
        "pipeline_id": governed_pipeline.get("pipeline_id"),
    }


def _blast_radius_from_handoff(handoff: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(handoff, dict):
        return {"risk_level": "low", "affected_files": []}
    plan = dict(handoff.get("plan") or {})
    steps = list(plan.get("steps") or [])
    files: list[str] = []
    for step in steps[:12]:
        if not isinstance(step, dict):
            continue
        target = step.get("target") or step.get("path")
        if target:
            files.append(str(target))
    risk = "medium" if len(steps) > 3 else "low"
    if handoff.get("risk_level") in {"low", "medium", "high"}:
        risk = str(handoff.get("risk_level"))
    return {"affected_files": files[:12], "risk_level": risk}


def append_pipeline_turn_event(
    session_id: str,
    *,
    governed_pipeline: dict[str, Any] | None,
    summary: str | None = None,
) -> dict[str, Any] | None:
    if not session_id or not isinstance(governed_pipeline, dict):
        return None
    pipeline_id = str(governed_pipeline.get("pipeline_id") or "")
    scope = _normalize_scope_id(session_id)
    parents: list[str] = []
    last_id = operator_decision_ledger_store.last_decision_id(scope)
    if last_id:
        parents = [last_id]
    return operator_decision_ledger_store.append(
        scope,
        {
            "decision_kind": "pipeline_turn",
            "decision": "allow",
            "reversibility": "undo_available",
            "session_id": session_id,
            "pipeline_id": pipeline_id or None,
            "causal_parents": parents,
            "blast_radius": {"risk_level": "low", "affected_files": []},
            "drift_context": _drift_context_from_pipeline(governed_pipeline),
            "summary": summary or f"Pipeline turn {pipeline_id or 'unknown'}",
        },
    )


def append_otem_approval_event(
    session_id: str,
    *,
    approval_id: str,
    decision: str,
    handoff: dict[str, Any] | None = None,
    pipeline_id: str | None = None,
    governed_pipeline: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not session_id or not approval_id:
        return None
    scope = _normalize_scope_id(session_id)
    parents: list[str] = []
    if decision in {"approve", "reject"}:
        pending_parent = operator_decision_ledger_store.find_pending_by_approval(scope, approval_id)
        if pending_parent:
            parents = [pending_parent]
    elif pipeline_id:
        pipeline_parent = operator_decision_ledger_store.find_by_pipeline(scope, pipeline_id)
        if pipeline_parent:
            parents = [pipeline_parent]
    else:
        last_id = operator_decision_ledger_store.last_decision_id(scope)
        if last_id:
            parents = [last_id]
    reversibility = "not_applicable" if decision == "reject" else "cannot_undo"
    if decision == "pending":
        reversibility = "undo_available"
    return operator_decision_ledger_store.append(
        scope,
        {
            "decision_kind": "otem_approval",
            "decision": decision,
            "reversibility": reversibility,
            "session_id": session_id,
            "approval_id": approval_id,
            "pipeline_id": pipeline_id,
            "causal_parents": parents,
            "blast_radius": _blast_radius_from_handoff(handoff),
            "drift_context": _drift_context_from_pipeline(governed_pipeline),
            "summary": f"OTEM execution approval {decision} ({approval_id[:8]})",
        },
    )


def append_urg_receipt_event(
    *,
    mission_id: str,
    tenant_id: str | None = None,
    session_id: str | None = None,
    outcome: str = "completed",
    federation: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not mission_id:
        return None
    scope = _normalize_scope_id(session_id or tenant_id or "global")
    parents: list[str] = []
    if session_id:
        last_id = operator_decision_ledger_store.last_decision_id(scope)
        if last_id:
            parents = [last_id]
    existing = operator_decision_ledger_store.find_by_mission(scope, mission_id)
    if existing:
        return operator_decision_ledger_store.get_event(scope, existing)
    decision = "completed" if outcome == "completed" else "failed"
    row: dict[str, Any] = {
        "decision_kind": "urg_receipt",
        "decision": decision,
        "reversibility": "cannot_undo",
        "session_id": session_id,
        "mission_id": mission_id,
        "tenant_id": tenant_id,
        "causal_parents": parents,
        "blast_radius": {"risk_level": "medium" if federation else "low", "affected_files": []},
        "drift_context": {"drift_band": "nominal"},
        "summary": f"URG mission receipt {decision} ({mission_id[:8]})",
    }
    if federation:
        row["federation"] = federation
    return operator_decision_ledger_store.append(scope, row)


def append_plug_execution_event(
    session_id: str,
    *,
    plug_id: str,
    decision: str | None = None,
    outcome: str | None = None,
    execution_id: str | None = None,
    source_kind: str = "",
    authority_level: str = "",
    mcp_server: str | None = None,
    blast_radius: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not plug_id:
        return None
    scope = _normalize_scope_id(session_id)
    parents: list[str] = []
    last_id = operator_decision_ledger_store.last_decision_id(scope)
    if last_id:
        parents = [last_id]
    raw = str(decision or outcome or "completed").strip().lower()
    if raw in {"ok", "success", "executed", "completed"}:
        raw = "allow"
    elif raw in {"blocked", "error"}:
        raw = "failed"
    normalized_decision = raw if raw in _DECISIONS else "failed"
    summary = f"Plug execution {normalized_decision}: {plug_id}"
    if execution_id:
        summary = f"{summary} ({execution_id[:12]})"
    return operator_decision_ledger_store.append(
        scope,
        {
            "decision_kind": "plug_execution",
            "decision": normalized_decision,
            "reversibility": "not_applicable",
            "session_id": session_id,
            "causal_parents": parents,
            "blast_radius": _bounded_blast_radius(blast_radius),
            "summary": summary,
            "event_context": {
                "plug_id": _clip_text(plug_id, 256),
                "execution_id": _clip_text(execution_id, 128) if execution_id else None,
                "source_kind": _clip_text(source_kind, 64),
                "authority_level": _clip_text(authority_level, 32),
                "mcp_server": _clip_text(mcp_server, 128) if mcp_server else None,
            },
        },
    )


def append_brain_decision_event(
    session_id: str,
    *,
    decision: str,
    session: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Record operator brain session consent decision (accept/reject/defer)."""
    if not session_id:
        return None
    mapping = {
        "accept": "approve",
        "accepted": "approve",
        "reject": "reject",
        "rejected": "reject",
        "defer": "defer",
        "deferred": "defer",
        "pending": "pending",
    }
    normalized = mapping.get(str(decision or "").strip().lower(), "pending")
    scope = _normalize_scope_id(session_id)
    parents: list[str] = []
    last_id = operator_decision_ledger_store.last_decision_id(scope)
    if last_id:
        parents = [last_id]
    proposal_id = None
    if isinstance(session, dict):
        proposal_id = session.get("active_proposal_id")
    reversibility = "undo_available" if normalized == "defer" else "not_applicable"
    if normalized == "reject":
        reversibility = "undo_available"
    return operator_decision_ledger_store.append(
        scope,
        {
            "decision_kind": "brain_decision",
            "decision": normalized,
            "reversibility": reversibility,
            "session_id": session_id,
            "causal_parents": parents,
            "blast_radius": {"risk_level": "low", "affected_files": []},
            "drift_context": {"drift_band": "nominal"},
            "summary": f"Brain session decision {normalized}"
            + (f" (proposal {proposal_id})" if proposal_id else ""),
        },
    )


def append_checkpoint_block_event(
    session_id: str,
    *,
    reason: str,
    drift_context: dict[str, Any] | None = None,
    approval_id: str | None = None,
) -> dict[str, Any] | None:
    scope = _normalize_scope_id(session_id)
    parents: list[str] = []
    last_id = operator_decision_ledger_store.last_decision_id(scope)
    if last_id:
        parents = [last_id]
    return operator_decision_ledger_store.append(
        scope,
        {
            "decision_kind": "checkpoint_block",
            "decision": "block",
            "reversibility": "not_applicable",
            "session_id": session_id,
            "approval_id": approval_id,
            "causal_parents": parents,
            "blast_radius": {"risk_level": "high", "affected_files": []},
            "drift_context": _bounded_drift_context(drift_context),
            "summary": _clip_text(reason, 500),
            "claim_label": "proven",
        },
    )


def evaluate_checkpoint_policy(event_context: dict[str, Any]) -> dict[str, Any]:
    """Return allow|block|defer with reason for irreversible execution paths."""
    if not checkpoint_policy_enabled():
        return {"action": "allow", "reason": "checkpoint policy disabled"}

    drift = _bounded_drift_context(event_context.get("drift_context"))
    if drift.get("drift_band") == "critical":
        return {
            "action": "block",
            "reason": "continuity witness drift_band is critical",
            "drift_context": drift,
        }

    intent_posture = str(event_context.get("agency_claim_posture") or "").strip().lower()
    if intent_posture == "rejected":
        return {
            "action": "block",
            "reason": "intent agency claim posture is rejected",
        }

    blast = _bounded_blast_radius(event_context.get("blast_radius"))
    decision_kind = str(event_context.get("decision_kind") or "")
    decision = str(event_context.get("decision") or "")
    execution_mode = str(event_context.get("execution_mode") or "").strip().upper()
    has_federation = bool(event_context.get("federation"))

    if (
        decision_kind == "otem_approval"
        and decision == "approve"
        and blast.get("risk_level") == "high"
    ):
        try:
            level = int(os.getenv("AAIS_OTEM_CAPABILITY_LEVEL", "10"))
        except ValueError:
            level = 10
        if level >= 10:
            return {
                "action": "defer",
                "reason": "high blast_radius OTEM approval requires additional review",
                "blast_radius": blast,
            }

    if execution_mode == "LIVE" and has_federation:
        digest = str((event_context.get("federation") or {}).get("federation_digest") or "")
        if not digest:
            return {
                "action": "block",
                "reason": "LIVE federated execution requires federation_digest",
            }

    return {"action": "allow", "reason": "policy checks passed"}


def _risk_level_change(before: str, after: str) -> str | None:
    if before == after:
        return None
    return f"{before}->{after}"


def build_decision_diff(scope_id: str, from_id: str, to_id: str) -> dict[str, Any]:
    """Synchronous field comparison between two ledger decisions."""
    scope = _normalize_scope_id(scope_id)
    from_row = operator_decision_ledger_store.get_event(scope, from_id)
    to_row = operator_decision_ledger_store.get_event(scope, to_id)
    if not from_row or not to_row:
        return {
            "scope_id": scope,
            "from_id": from_id,
            "to_id": to_id,
            "found": False,
            "error": "one or both decisions not found",
        }

    from_blast = dict(from_row.get("blast_radius") or {})
    to_blast = dict(to_row.get("blast_radius") or {})
    from_files = set(str(f) for f in list(from_blast.get("affected_files") or []))
    to_files = set(str(f) for f in list(to_blast.get("affected_files") or []))
    from_drift = dict(from_row.get("drift_context") or {})
    to_drift = dict(to_row.get("drift_context") or {})
    from_fed = dict(from_row.get("federation") or {})
    to_fed = dict(to_row.get("federation") or {})
    from_grant = str(from_fed.get("grant_id") or (from_fed.get("counterparty_receipt_ref") or {}).get("grant_id") or "")
    to_grant = str(to_fed.get("grant_id") or (to_fed.get("counterparty_receipt_ref") or {}).get("grant_id") or "")

    from_pipeline = str(from_row.get("pipeline_id") or from_drift.get("pipeline_id") or "")
    to_pipeline = str(to_row.get("pipeline_id") or to_drift.get("pipeline_id") or "")

    from_kind = str(from_row.get("decision_kind") or "")
    to_kind = str(to_row.get("decision_kind") or "")

    return {
        "scope_id": scope,
        "from_id": from_id,
        "to_id": to_id,
        "found": True,
        "blast_radius_delta": {
            "added_files": sorted(to_files - from_files),
            "removed_files": sorted(from_files - to_files),
            "risk_level_change": _risk_level_change(
                str(from_blast.get("risk_level") or "low"),
                str(to_blast.get("risk_level") or "low"),
            ),
        },
        "drift_delta": {
            "drift_band_change": _risk_level_change(
                str(from_drift.get("drift_band") or "idle"),
                str(to_drift.get("drift_band") or "idle"),
            ),
            "trajectory_status_change": _risk_level_change(
                str(from_drift.get("trajectory_status") or ""),
                str(to_drift.get("trajectory_status") or ""),
            ),
        },
        "federation_delta": {
            "digest_changed": str(from_fed.get("federation_digest") or "")
            != str(to_fed.get("federation_digest") or ""),
            "grant_id_changed": from_grant != to_grant,
        },
        "pipeline_ids": {
            "from": from_pipeline or None,
            "to": to_pipeline or None,
        },
        "decision_kind_change": (
            f"{from_kind}->{to_kind}" if from_kind != to_kind else None
        ),
    }


def append_federated_peer_decision_event(
    home_scope: str,
    *,
    grant_id: str,
    federation_digest: str,
    counterparty_receipt_ref: dict[str, Any],
    parent_decision_id: str,
) -> dict[str, Any] | None:
    """Write peer-tenant ledger row linked to home receipt decision."""
    peer_tenant = str(counterparty_receipt_ref.get("tenant_id") or "").strip()
    if not peer_tenant:
        return None
    peer_scope = _normalize_scope_id(f"tenant:{peer_tenant.replace('tenant:', '')}")
    return operator_decision_ledger_store.append(
        peer_scope,
        {
            "decision_kind": "urg_receipt",
            "decision": "completed",
            "reversibility": "cannot_undo",
            "tenant_id": peer_tenant,
            "causal_parents": [parent_decision_id] if parent_decision_id else [],
            "blast_radius": {"risk_level": "medium", "affected_files": []},
            "drift_context": {"drift_band": "nominal"},
            "federation": {
                "federation_digest": federation_digest,
                "grant_id": grant_id,
                "counterparty_receipt_ref": counterparty_receipt_ref,
            },
            "summary": f"Federated peer stub ({grant_id[:8]})",
        },
    )


def _load_mission_ledger_rows(runtime_dir: Path, tenant_id: str, grant_id: str) -> list[dict[str, Any]]:
    from src.ugr.mission.mission_ledger import MissionLedger
    from src.ugr.mission.tenant_manifold import tenant_path_slug

    slug = tenant_path_slug(tenant_id)
    path = runtime_dir / "collective-pattern-ledger" / "tenants" / slug / "missions.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            row_grant = str(row.get("federation_grant_id") or row.get("grant_id") or "")
            if row_grant == grant_id:
                rows.append(row)
    return rows


def build_federation_graph(
    grant_id: str,
    *,
    home_tenant_id: str | None = None,
    home_scope: str | None = None,
) -> dict[str, Any]:
    """Merge home + peer operator ledger nodes for a federation grant."""
    scope = _normalize_scope_id(home_scope or home_tenant_id or "global")
    rows = operator_decision_ledger_store._read_rows(scope)
    home_rows = [
        r
        for r in rows
        if str((r.get("federation") or {}).get("grant_id") or "")
        == grant_id
        or str(((r.get("federation") or {}).get("counterparty_receipt_ref") or {}).get("grant_id") or "")
        == grant_id
    ]

    digest_verified = False
    peer_nodes: list[dict[str, Any]] = []
    peer_scope: str | None = None
    runtime_dir = operator_decision_ledger_store.runtime_dir

    home_nodes = [
        {
            "decision_id": str(r.get("decision_id") or ""),
            "decision_kind": r.get("decision_kind"),
            "decision": r.get("decision"),
            "scope_id": scope,
            "tenant_id": r.get("tenant_id"),
            "summary": r.get("summary"),
        }
        for r in home_rows[:MAX_GRAPH_NODES]
    ]
    edges: list[dict[str, str]] = []
    for row in home_rows:
        did = str(row.get("decision_id") or "")
        for parent in list(row.get("causal_parents") or []):
            edges.append({"from": str(parent), "to": did, "scope": scope})

    if home_rows:
        federation = dict(home_rows[0].get("federation") or {})
        counterparty_ref = dict(federation.get("counterparty_receipt_ref") or {})
        stored_digest = str(federation.get("federation_digest") or "")
        peer_tenant = str(counterparty_ref.get("tenant_id") or home_tenant_id or "").strip()

        if peer_tenant:
            peer_scope = _normalize_scope_id(f"tenant:{peer_tenant.replace('tenant:', '')}")
            peer_ledger_rows = operator_decision_ledger_store._read_rows(peer_scope)
            peer_matches = [
                r
                for r in peer_ledger_rows
                if str((r.get("federation") or {}).get("grant_id") or "") == grant_id
            ]
            for row in peer_matches[:MAX_GRAPH_NODES]:
                did = str(row.get("decision_id") or "")
                peer_nodes.append(
                    {
                        "decision_id": did,
                        "decision_kind": row.get("decision_kind"),
                        "decision": row.get("decision"),
                        "scope_id": peer_scope,
                        "tenant_id": row.get("tenant_id"),
                        "summary": row.get("summary"),
                    }
                )
                for parent in list(row.get("causal_parents") or []):
                    edges.append({"from": str(parent), "to": did, "scope": peer_scope})
                for home_row in home_rows:
                    home_id = str(home_row.get("decision_id") or "")
                    if home_id in [str(p) for p in list(row.get("causal_parents") or [])]:
                        edges.append({"from": home_id, "to": did, "scope": "cross"})

        if stored_digest and peer_tenant and runtime_dir.is_dir():
            try:
                from src.ugr.mission.federation_grants import compute_federation_digest

                home_ledger = _load_mission_ledger_rows(runtime_dir, peer_tenant, grant_id)
                if home_tenant_id:
                    home_mission_rows = _load_mission_ledger_rows(runtime_dir, home_tenant_id, grant_id)
                else:
                    home_mission_rows = []
                computed = compute_federation_digest(
                    home_rows=home_mission_rows or home_ledger,
                    peer_rows=home_ledger,
                    grant_id=grant_id,
                )
                digest_verified = computed == stored_digest
            except Exception:
                digest_verified = False

        if counterparty_ref and peer_tenant:
            try:
                from src.ugr.mission.mission_receipt_store import MissionReceiptStore

                home_tid = str(home_tenant_id or rows[0].get("tenant_id") or "default")
                store = MissionReceiptStore(runtime_dir=str(runtime_dir), tenant_id=home_tid)
                stub = store.resolve_counterparty_ref(counterparty_ref)
                if stub and home_rows:
                    parent_id = str(home_rows[0].get("decision_id") or "")
                    append_federated_peer_decision_event(
                        scope,
                        grant_id=grant_id,
                        federation_digest=stored_digest,
                        counterparty_receipt_ref=counterparty_ref,
                        parent_decision_id=parent_id,
                    )
            except Exception:
                pass

    total_nodes = len(home_nodes) + len(peer_nodes)
    truncated = total_nodes >= MAX_GRAPH_NODES
    return {
        "grant_id": grant_id,
        "home_scope": scope,
        "peer_scope": peer_scope,
        "digest_verified": digest_verified,
        "home_nodes": home_nodes,
        "peer_nodes": peer_nodes,
        "edges": edges[:MAX_GRAPH_NODES * 2],
        "truncated": truncated,
        "node_count": total_nodes,
    }


def build_operator_decision_ledger_status(
    scope_id: str | None = None,
) -> dict[str, Any]:
    scope = _normalize_scope_id(scope_id)
    summary = operator_decision_ledger_store.build_digest_summary(scope)
    path = operator_ledger_path(scope, runtime_dir=operator_decision_ledger_store.runtime_dir)
    return {
        "operator_decision_ledger_version": LEDGER_VERSION,
        "module_id": MODULE_ID,
        "entry_count": summary["entry_count"],
        "pending_count": summary["pending_count"],
        "cannot_undo_count": summary["cannot_undo_count"],
        "cross_tenant_decisions_count": summary["cross_tenant_decisions_count"],
        "latest_drift_band": summary["latest_drift_band"],
        "latest_decision_id": summary.get("latest_decision_id"),
        "ledger_path": str(path),
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
