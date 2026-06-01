"""Forgekeeper Stage 1/2 runtime skeleton with dry-run defaults."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Literal


ClaimLabel = Literal["asserted", "proven", "rejected"]
GateDecision = Literal["approve", "reject"]

ALLOWED_MODES = {
    "observe",
    "judge",
    "plan",
    "status",
    "report",
    "snapshot",
    "snapshot-index",
    "snapshot-query",
    "trace-query",
    "reconcile-query",
    "drift-window-query",
    "verify",
    "chaos-check",
    "bundle-export",
    "reconcile-artifacts",
}


@dataclass(slots=True)
class ForgekeeperRequest:
    """Bounded request shape used by stage 1/2 skeleton commands."""

    plan_id: str
    goal: str
    scope: str
    focus_files: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    context_files: dict[str, str] = field(default_factory=dict)

    def normalized_focus_files(self) -> list[str]:
        names = [item.strip() for item in self.focus_files if item.strip()]
        return sorted(set(names))


@dataclass(slots=True)
class AttestationHook:
    """Preflight attestation record."""

    hook_name: str
    status: ClaimLabel
    message: str


@dataclass(slots=True)
class ChangeNode:
    """One node in a deterministic change graph."""

    node_id: str
    file_path: str
    action: str
    rationale: str
    content_hash: str


@dataclass(slots=True)
class ChangeEdge:
    """One directed edge in the dry-run change graph."""

    source: str
    target: str
    relation: str


@dataclass(slots=True)
class DryRunPlan:
    """Serializable dry-run plan output for stage 2 scaffolding."""

    plan_id: str
    mode: str
    generated_at_utc: str
    deterministic_seed: str
    scope: str
    goal: str
    claim_label: ClaimLabel
    safety_state: str
    rollback_token: str
    attestation_overall: ClaimLabel
    attestation_hooks: list[AttestationHook] = field(default_factory=list)
    change_nodes: list[ChangeNode] = field(default_factory=list)
    change_edges: list[ChangeEdge] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class JudgeResult:
    """Read-only governance decision record."""

    plan_id: str
    decision: GateDecision
    reason: str
    reviewer: str
    mode: str
    claim_label: ClaimLabel
    safety_state: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DecisionLedgerRecord:
    """Stage 3-safe scaffold record for governance decisions."""

    record_id: str
    mode: str
    plan_id: str
    decision: GateDecision
    claim_status: ClaimLabel
    claim_label: ClaimLabel
    reviewer: str
    reason: str
    recorded_at_utc: str
    attestation_state: str
    evidence_refs: list[str] = field(default_factory=list)
    ledger_version: str = "forgekeeper.ledger.v1"

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


class ForgekeeperError(ValueError):
    """Raised when a Forgekeeper request violates stage gate constraints."""


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _seed_for_request(request: ForgekeeperRequest) -> str:
    payload = {
        "plan_id": request.plan_id,
        "goal": request.goal,
        "scope": request.scope,
        "focus_files": request.normalized_focus_files(),
        "constraint_keys": sorted(str(item) for item in request.constraints.keys()),
    }
    return _hash_text(json.dumps(payload, sort_keys=True))


def _build_change_nodes(request: ForgekeeperRequest, seed: str) -> list[ChangeNode]:
    nodes: list[ChangeNode] = []
    for index, file_path in enumerate(request.normalized_focus_files()):
        content = request.context_files.get(file_path, "")
        content_hash = _hash_text(content)
        node_id = f"node-{index + 1:03d}"
        nodes.append(
            ChangeNode(
                node_id=node_id,
                file_path=file_path,
                action="proposed_update",
                rationale=f"dry-run placeholder for goal: {request.goal}",
                content_hash=content_hash,
            )
        )

    if not nodes:
        nodes.append(
            ChangeNode(
                node_id="node-001",
                file_path=request.scope,
                action="observe_only",
                rationale="no focus files provided; plan is observation-only",
                content_hash=seed,
            )
        )
    return nodes


def _build_change_edges(nodes: list[ChangeNode]) -> list[ChangeEdge]:
    edges: list[ChangeEdge] = []
    for idx in range(len(nodes) - 1):
        edges.append(
            ChangeEdge(
                source=nodes[idx].node_id,
                target=nodes[idx + 1].node_id,
                relation="ordered_after",
            )
        )
    return edges


def _validate_scope(scope: str) -> bool:
    text = scope.strip()
    if not text:
        return False
    if text.startswith("/") or text.startswith("\\"):
        return False
    if ":" in text:
        return False
    return ".." not in text.split("/")


def evaluate_attestation_hooks(request: ForgekeeperRequest) -> list[AttestationHook]:
    """Run deterministic preflight attestations for stage 2 planning."""

    hooks: list[AttestationHook] = []
    no_apply = bool(request.constraints.get("no_apply", True))
    hooks.append(
        AttestationHook(
            hook_name="law_precheck",
            status="proven" if no_apply else "rejected",
            message=(
                "non-destructive policy confirmed"
                if no_apply
                else "request attempted to disable non-destructive policy"
            ),
        )
    )

    scope_ok = _validate_scope(request.scope)
    hooks.append(
        AttestationHook(
            hook_name="scope_boundary_precheck",
            status="proven" if scope_ok else "rejected",
            message=(
                "scope is bounded and relative"
                if scope_ok
                else "scope is unbounded or unsafe"
            ),
        )
    )

    evidence_ref = str(request.constraints.get("proof_bundle_ref", "")).strip()
    hooks.append(
        AttestationHook(
            hook_name="evidence_reference_precheck",
            status="proven" if evidence_ref else "asserted",
            message=(
                f"proof reference provided: {evidence_ref}"
                if evidence_ref
                else "proof reference missing; evidence linkage still asserted"
            ),
        )
    )
    return hooks


def derive_attestation_overall(hooks: list[AttestationHook]) -> ClaimLabel:
    """Derive overall claim label from hook outcomes."""

    statuses = {item.status for item in hooks}
    if "rejected" in statuses:
        return "rejected"
    if statuses == {"proven"}:
        return "proven"
    return "asserted"


def _enforce_mode(mode: str) -> None:
    if mode not in ALLOWED_MODES:
        allowed = ", ".join(sorted(ALLOWED_MODES))
        raise ForgekeeperError(f"mode must be one of: {allowed}")


def _enforce_non_destructive(mode: str, allow_apply: bool) -> None:
    if allow_apply:
        raise ForgekeeperError("apply mode is disabled in stage 1/2; dry-run only.")
    if mode not in {
        "observe",
        "judge",
        "plan",
        "status",
        "report",
        "snapshot",
        "snapshot-index",
        "snapshot-query",
        "trace-query",
        "reconcile-query",
        "drift-window-query",
        "verify",
        "chaos-check",
        "bundle-export",
        "reconcile-artifacts",
    }:
        raise ForgekeeperError("unsupported execution mode.")


def build_dry_run_plan(request: ForgekeeperRequest, *, mode: str = "plan") -> DryRunPlan:
    """Return a deterministic dry-run plan scaffold for stage 2."""

    _enforce_mode(mode)
    seed = _seed_for_request(request)
    nodes = _build_change_nodes(request, seed)
    edges = _build_change_edges(nodes)
    rollback_token = f"rbk-{seed[:16]}"
    hooks = evaluate_attestation_hooks(request)
    attestation_overall = derive_attestation_overall(hooks)
    return DryRunPlan(
        plan_id=request.plan_id,
        mode=mode,
        generated_at_utc=datetime.now(UTC).isoformat(),
        deterministic_seed=seed,
        scope=request.scope,
        goal=request.goal,
        claim_label=attestation_overall,
        safety_state="dry_run_only",
        rollback_token=rollback_token,
        attestation_overall=attestation_overall,
        attestation_hooks=hooks,
        change_nodes=nodes,
        change_edges=edges,
        notes=[
            "non-destructive stage 2 scaffold",
            "execution path intentionally gated off",
        ],
    )


def observe_request(request: ForgekeeperRequest) -> dict[str, Any]:
    """Return read-only observation summary for stage 1."""

    return {
        "plan_id": request.plan_id,
        "scope": request.scope,
        "goal": request.goal,
        "focus_files": request.normalized_focus_files(),
        "mode": "observe",
        "claim_label": "asserted",
        "safety_state": "read_only",
    }


def judge_request(
    request: ForgekeeperRequest,
    *,
    decision: GateDecision,
    reason: str,
    reviewer: str,
    allow_approve: bool = False,
) -> JudgeResult:
    """Return read-only governance judgment with strict approve gating."""

    if decision == "approve" and not allow_approve:
        raise ForgekeeperError("approve decision requires --allow-approve flag.")
    if decision == "approve" and not reviewer.strip():
        raise ForgekeeperError("approve decision requires reviewer identity.")
    claim_label: ClaimLabel = "asserted" if decision == "approve" else "rejected"
    return JudgeResult(
        plan_id=request.plan_id,
        decision=decision,
        reason=reason.strip() or "no reason provided",
        reviewer=reviewer.strip() or "unassigned",
        mode="judge",
        claim_label=claim_label,
        safety_state="read_only_gate",
    )


def build_decision_record(result: JudgeResult) -> DecisionLedgerRecord:
    """Build a serializable stage 3 ledger placeholder from judge output."""

    record_seed = _hash_text(
        json.dumps(
            {
                "plan_id": result.plan_id,
                "decision": result.decision,
                "reviewer": result.reviewer,
                "reason": result.reason,
            },
            sort_keys=True,
        )
    )
    return DecisionLedgerRecord(
        record_id=f"ledger-{record_seed[:12]}",
        mode=result.mode,
        plan_id=result.plan_id,
        decision=result.decision,
        claim_status=result.claim_label,
        claim_label=result.claim_label,
        reviewer=result.reviewer,
        reason=result.reason,
        recorded_at_utc=datetime.now(UTC).isoformat(),
        attestation_state="asserted",
    )


def append_decision_record(record: DecisionLedgerRecord, ledger_path: Path) -> None:
    """Append a decision record to a JSONL ledger."""

    target = ledger_path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record.model_dump(), sort_keys=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(payload)
        handle.write("\n")


def ledger_summary(ledger_path: Path) -> dict[str, Any]:
    """Return a lightweight summary of an append-only decision ledger."""

    target = ledger_path.expanduser().resolve()
    if not target.exists():
        return {"exists": False, "entries": 0}
    lines = [line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {"exists": True, "entries": 0}
    last = json.loads(lines[-1])
    return {
        "exists": True,
        "entries": len(lines),
        "last_record_id": last.get("record_id"),
        "last_claim_status": last.get("claim_status"),
    }


def read_ledger_entries(ledger_path: Path, *, tail: int = 5) -> list[dict[str, Any]]:
    """Read tail entries from an append-only JSONL decision ledger."""

    target = ledger_path.expanduser().resolve()
    if not target.exists():
        return []
    lines = [line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = lines[-max(1, int(tail)) :]
    entries: list[dict[str, Any]] = []
    for line in selected:
        entries.append(json.loads(line))
    return entries


def latest_plan_artifact(proof_dir: Path) -> Path | None:
    """Return the newest likely plan artifact from the proof directory."""

    root = proof_dir.expanduser().resolve()
    if not root.exists():
        return None
    candidates = sorted(
        [item for item in root.glob("*plan*.json") if item.is_file()],
        key=lambda item: (item.stat().st_mtime, item.name),
        reverse=True,
    )
    return candidates[0] if candidates else None


def derive_claim_status(statuses: list[ClaimLabel]) -> ClaimLabel:
    """Derive one claim label from component claim labels."""

    if "rejected" in statuses:
        return "rejected"
    if "asserted" in statuses:
        return "asserted"
    return "proven"


def build_snapshot_index(
    *,
    report_path: Path,
    ledger_path: Path,
    evidence_refs: list[str],
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build immutable snapshot metadata linking report and ledger state."""

    created_at = created_at_utc or datetime.now(UTC).isoformat()
    report_target = report_path.expanduser().resolve()
    ledger_target = ledger_path.expanduser().resolve()

    report_exists = report_target.exists()
    report_hash = _sha256_file(report_target) if report_exists else ""
    report_claim: ClaimLabel = "rejected"
    if report_exists:
        try:
            report_payload = json.loads(report_target.read_text(encoding="utf-8"))
            parsed_claim = str(report_payload.get("claim_label") or "asserted")
            report_claim = parsed_claim if parsed_claim in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            report_claim = "rejected"

    ledger_info = ledger_summary(ledger_target)
    ledger_exists = bool(ledger_info.get("exists"))
    ledger_entries = int(ledger_info.get("entries") or 0)
    ledger_hash = _sha256_file(ledger_target) if ledger_exists else ""
    ledger_claim: ClaimLabel = "proven" if ledger_entries > 0 else ("asserted" if ledger_exists else "rejected")

    evidence_items: list[dict[str, Any]] = []
    evidence_statuses: list[ClaimLabel] = []
    for item in sorted({ref.strip() for ref in evidence_refs if ref.strip()}):
        target = Path(item).expanduser().resolve()
        exists = target.exists()
        claim: ClaimLabel = "proven" if exists else "rejected"
        evidence_statuses.append(claim)
        evidence_items.append(
            {
                "ref": item,
                "path": str(target),
                "exists": exists,
                "claim_label": claim,
                "sha256": _sha256_file(target) if exists and target.is_file() else "",
            }
        )
    evidence_claim = derive_claim_status(evidence_statuses) if evidence_statuses else "asserted"

    overall = derive_claim_status([report_claim, ledger_claim, evidence_claim])
    snapshot_seed = _hash_text(
        _json_stable(
            {
                "created_at_utc": created_at,
                "report_sha256": report_hash,
                "ledger_sha256": ledger_hash,
                "evidence_paths": [item["path"] for item in evidence_items],
                "claim_label": overall,
            },
            pretty=False,
        )
    )
    snapshot_id = f"snap-{snapshot_seed[:16]}"
    return {
        "snapshot_version": "forgekeeper.snapshot.v1",
        "snapshot_id": snapshot_id,
        "created_at_utc": created_at,
        "claim_label": overall,
        "immutable_metadata": True,
        "report": {
            "path": str(report_target),
            "exists": report_exists,
            "sha256": report_hash,
            "claim_label": report_claim,
        },
        "ledger": {
            "path": str(ledger_target),
            "exists": ledger_exists,
            "entries": ledger_entries,
            "sha256": ledger_hash,
            "claim_label": ledger_claim,
            "last_record_id": ledger_info.get("last_record_id", ""),
        },
        "evidence_refs": {
            "claim_label": evidence_claim,
            "items": evidence_items,
        },
        "linkage": {
            "report_hash": report_hash,
            "ledger_hash": ledger_hash,
            "evidence_refs": [item["ref"] for item in evidence_items],
        },
    }


def snapshot_index_summary(index_path: Path) -> dict[str, Any]:
    """Return a lightweight summary of the append-only snapshot index."""

    target = index_path.expanduser().resolve()
    if not target.exists():
        return {"exists": False, "entries": 0}
    lines = [line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {"exists": True, "entries": 0}
    last = json.loads(lines[-1])
    return {
        "exists": True,
        "entries": len(lines),
        "last_index_id": str(last.get("index_id") or ""),
        "last_snapshot_id": str(last.get("snapshot_id") or ""),
        "last_claim_transition": str(last.get("claim_transition") or ""),
    }


def _read_last_snapshot_index_entry(index_path: Path) -> dict[str, Any] | None:
    target = index_path.expanduser().resolve()
    if not target.exists():
        return None
    lines = [line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def _read_snapshot_index_entries(index_path: Path) -> list[dict[str, Any]]:
    target = index_path.expanduser().resolve()
    if not target.exists():
        return []
    lines = [line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    entries: list[dict[str, Any]] = []
    for line in lines:
        entries.append(json.loads(line))
    return entries


def query_snapshot_index(
    *,
    index_path: Path,
    snapshot_id: str = "",
    claim_label: str = "",
    since_utc: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Query append-only snapshot index records with deterministic filtering."""

    target = index_path.expanduser().resolve()
    exists = target.exists()
    if not exists:
        return {
            "mode": "snapshot-query",
            "index_path": str(target),
            "claim_label": "rejected",
            "filters": {
                "snapshot_id": snapshot_id.strip(),
                "claim_label": claim_label.strip(),
                "since_utc": since_utc.strip(),
                "limit": max(1, int(limit)),
            },
            "matched_count": 0,
            "total_entries": 0,
            "results": [],
        }

    claim_filter = claim_label.strip().lower()
    if claim_filter and claim_filter not in {"asserted", "proven", "rejected"}:
        raise ForgekeeperError("query claim label must be asserted, proven, or rejected.")

    snapshot_filter = snapshot_id.strip()
    since_value = since_utc.strip()
    max_items = max(1, int(limit))
    entries = _read_snapshot_index_entries(target)
    filtered: list[dict[str, Any]] = []
    for item in entries:
        if snapshot_filter and str(item.get("snapshot_id") or "") != snapshot_filter:
            continue
        if claim_filter and str(item.get("claim_label") or "") != claim_filter:
            continue
        item_time = str(item.get("created_at_utc") or "")
        if since_value and item_time < since_value:
            continue
        filtered.append(item)

    filtered = filtered[-max_items:]
    claim = "proven" if filtered else "asserted"
    return {
        "mode": "snapshot-query",
        "index_path": str(target),
        "claim_label": claim,
        "filters": {
            "snapshot_id": snapshot_filter,
            "claim_label": claim_filter,
            "since_utc": since_value,
            "limit": max_items,
        },
        "matched_count": len(filtered),
        "total_entries": len(entries),
        "results": filtered,
        "summary": {
            "latest_transition": str(filtered[-1].get("claim_transition") or "") if filtered else "",
            "latest_index_id": str(filtered[-1].get("index_id") or "") if filtered else "",
        },
    }


def query_governance_trace(
    *,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
    index_path: Path,
    ledger_claim_status: str = "",
    reviewer: str = "",
    since_utc: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Query and correlate governance artifacts in read-only mode."""

    claim_filter = ledger_claim_status.strip().lower()
    if claim_filter and claim_filter not in {"asserted", "proven", "rejected"}:
        raise ForgekeeperError("trace query claim status must be asserted, proven, or rejected.")

    reviewer_filter = reviewer.strip()
    since_value = since_utc.strip()
    max_items = max(1, int(limit))
    ledger_target = ledger_path.expanduser().resolve()
    report_target = report_path.expanduser().resolve()
    snapshot_target = snapshot_path.expanduser().resolve()
    index_target = index_path.expanduser().resolve()

    all_ledger_entries = read_ledger_entries(ledger_target, tail=1000000)
    filtered_ledger: list[dict[str, Any]] = []
    for entry in all_ledger_entries:
        if claim_filter and str(entry.get("claim_status") or "") != claim_filter:
            continue
        if reviewer_filter and str(entry.get("reviewer") or "") != reviewer_filter:
            continue
        entry_time = str(entry.get("recorded_at_utc") or "")
        if since_value and entry_time < since_value:
            continue
        filtered_ledger.append(entry)
    filtered_ledger = filtered_ledger[-max_items:]
    ledger_claim: ClaimLabel = "proven" if filtered_ledger else ("asserted" if ledger_target.exists() else "rejected")

    report_exists = report_target.exists()
    report_hash = _sha256_file(report_target) if report_exists else ""
    report_claim: ClaimLabel = "rejected"
    report_payload: dict[str, Any] = {}
    if report_exists:
        try:
            report_payload = json.loads(report_target.read_text(encoding="utf-8"))
            parsed = str(report_payload.get("claim_label") or "asserted")
            report_claim = parsed if parsed in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            report_claim = "rejected"

    snapshot_exists = snapshot_target.exists()
    snapshot_hash = _sha256_file(snapshot_target) if snapshot_exists else ""
    snapshot_claim: ClaimLabel = "rejected"
    snapshot_payload: dict[str, Any] = {}
    if snapshot_exists:
        try:
            snapshot_payload = json.loads(snapshot_target.read_text(encoding="utf-8"))
            parsed = str(snapshot_payload.get("claim_label") or "asserted")
            snapshot_claim = parsed if parsed in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            snapshot_claim = "rejected"

    index_entries = _read_snapshot_index_entries(index_target)
    latest_index = index_entries[-1] if index_entries else {}
    index_claim: ClaimLabel = "proven" if index_entries else ("asserted" if index_target.exists() else "rejected")

    linkage_checks = [
        {
            "name": "snapshot_report_hash_match",
            "expected": report_hash,
            "actual": str((snapshot_payload.get("linkage") or {}).get("report_hash") or ""),
        },
        {
            "name": "snapshot_ledger_hash_match",
            "expected": _sha256_file(ledger_target) if ledger_target.exists() else "",
            "actual": str((snapshot_payload.get("linkage") or {}).get("ledger_hash") or ""),
        },
        {
            "name": "index_report_hash_match",
            "expected": report_hash,
            "actual": str(latest_index.get("report_sha256") or ""),
        },
        {
            "name": "index_ledger_hash_match",
            "expected": _sha256_file(ledger_target) if ledger_target.exists() else "",
            "actual": str(latest_index.get("ledger_sha256") or ""),
        },
        {
            "name": "index_snapshot_hash_match",
            "expected": snapshot_hash,
            "actual": str(latest_index.get("snapshot_sha256") or ""),
        },
    ]
    linkage_statuses: list[ClaimLabel] = []
    for item in linkage_checks:
        expected = str(item["expected"])
        actual = str(item["actual"])
        if not expected:
            item["claim_label"] = "asserted"
        elif expected == actual:
            item["claim_label"] = "proven"
        else:
            item["claim_label"] = "rejected"
        linkage_statuses.append(item["claim_label"])
    linkage_claim = derive_claim_status(linkage_statuses)
    overall = derive_claim_status([ledger_claim, report_claim, snapshot_claim, index_claim, linkage_claim])

    return {
        "mode": "trace-query",
        "claim_label": overall,
        "filters": {
            "ledger_claim_status": claim_filter,
            "reviewer": reviewer_filter,
            "since_utc": since_value,
            "limit": max_items,
        },
        "ledger": {
            "path": str(ledger_target),
            "summary": ledger_summary(ledger_target),
            "claim_label": ledger_claim,
            "matched_count": len(filtered_ledger),
            "results": filtered_ledger,
        },
        "report": {
            "path": str(report_target),
            "exists": report_exists,
            "sha256": report_hash,
            "claim_label": report_claim,
            "generated_at_utc": str(report_payload.get("generated_at_utc") or ""),
        },
        "snapshot": {
            "path": str(snapshot_target),
            "exists": snapshot_exists,
            "sha256": snapshot_hash,
            "claim_label": snapshot_claim,
            "snapshot_id": str(snapshot_payload.get("snapshot_id") or ""),
        },
        "snapshot_index": {
            "path": str(index_target),
            "entries": len(index_entries),
            "claim_label": index_claim,
            "latest_index_id": str(latest_index.get("index_id") or ""),
            "latest_transition": str(latest_index.get("claim_transition") or ""),
        },
        "traceability_checks": {
            "claim_label": linkage_claim,
            "checks": linkage_checks,
        },
    }


def query_governance_reconciliation(
    *,
    plan_id: str,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
    index_path: Path,
    ledger_claim_status: str = "",
    reviewer: str = "",
    since_utc: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Emit read-only reconciliation hints when traceability checks drift."""

    trace = query_governance_trace(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
        ledger_claim_status=ledger_claim_status,
        reviewer=reviewer,
        since_utc=since_utc,
        limit=limit,
    )
    checks = list((trace.get("traceability_checks") or {}).get("checks") or [])
    drift_checks = [item for item in checks if str(item.get("claim_label") or "") == "rejected"]
    drift_names = {str(item.get("name") or "") for item in drift_checks}

    recommendations: list[dict[str, Any]] = []
    report_target = report_path.expanduser().resolve()
    snapshot_target = snapshot_path.expanduser().resolve()
    index_target = index_path.expanduser().resolve()
    ledger_target = ledger_path.expanduser().resolve()

    if not bool((trace.get("report") or {}).get("exists")):
        recommendations.append(
            {
                "action_id": "rebuild-report",
                "claim_label": "asserted",
                "reason": "report artifact missing",
                "command_template": (
                    "py -3.12 -m forge.forgekeeper --mode report "
                    f"--plan-id {plan_id} --report-path \"{report_target}\" --ledger-path \"{ledger_target}\""
                ),
            }
        )

    if not bool((trace.get("snapshot") or {}).get("exists")) or (
        "snapshot_report_hash_match" in drift_names or "snapshot_ledger_hash_match" in drift_names
    ):
        recommendations.append(
            {
                "action_id": "rebuild-snapshot",
                "claim_label": "asserted",
                "reason": "snapshot linkage is missing or drifted",
                "command_template": (
                    "py -3.12 -m forge.forgekeeper --mode snapshot "
                    f"--plan-id {plan_id} --report-path \"{report_target}\" "
                    f"--ledger-path \"{ledger_target}\" --snapshot-path \"{snapshot_target}\""
                ),
            }
        )

    if not bool((trace.get("snapshot_index") or {}).get("entries")) or (
        "index_report_hash_match" in drift_names
        or "index_ledger_hash_match" in drift_names
        or "index_snapshot_hash_match" in drift_names
    ):
        recommendations.append(
            {
                "action_id": "append-snapshot-index",
                "claim_label": "asserted",
                "reason": "snapshot index linkage is missing or drifted",
                "command_template": (
                    "py -3.12 -m forge.forgekeeper --mode snapshot-index "
                    f"--plan-id {plan_id} --snapshot-path \"{snapshot_target}\" "
                    f"--report-path \"{report_target}\" --ledger-path \"{ledger_target}\" "
                    f"--snapshot-index-path \"{index_target}\""
                ),
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "action_id": "no-action-required",
                "claim_label": "proven",
                "reason": "traceability checks are currently consistent",
                "command_template": "",
            }
        )

    recommendation_claim: ClaimLabel = "proven" if not drift_checks else "asserted"
    return {
        "mode": "reconcile-query",
        "plan_id": plan_id,
        "claim_label": str(trace.get("claim_label") or "asserted"),
        "recommendation_claim_label": recommendation_claim,
        "drift_count": len(drift_checks),
        "drift_checks": drift_checks,
        "recommendations": recommendations,
        "trace": trace,
    }


def traceability_drift_summary(
    *,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
    index_path: Path,
) -> dict[str, Any]:
    """Return a lightweight status-time drift summary without mutation."""

    trace = query_governance_trace(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
        limit=1,
    )
    checks = list((trace.get("traceability_checks") or {}).get("checks") or [])
    rejected_names = sorted(str(item.get("name") or "") for item in checks if str(item.get("claim_label") or "") == "rejected")
    return {
        "claim_label": str((trace.get("traceability_checks") or {}).get("claim_label") or "asserted"),
        "drift_detected": bool(rejected_names),
        "drift_checks": rejected_names,
    }


def query_drift_window(
    *,
    index_path: Path,
    since_utc: str = "",
    limit: int = 10,
    pair_only: bool = True,
) -> dict[str, Any]:
    """Analyze drift trend over a snapshot-index window.

    When pair_only is true (default), trend is derived from the latest two
    index entries only so historical append-only rows do not force degrading.
    """

    target = index_path.expanduser().resolve()
    if not target.exists():
        return {
            "mode": "drift-window-query",
            "index_path": str(target),
            "claim_label": "rejected",
            "since_utc": since_utc.strip(),
            "limit": max(1, int(limit)),
            "entries": 0,
            "trend": "missing_index",
            "trend_basis": "pair" if pair_only else "window",
            "window": [],
        }

    since_value = since_utc.strip()
    max_items = max(1, int(limit))
    entries = _read_snapshot_index_entries(target)
    filtered: list[dict[str, Any]] = []
    for item in entries:
        item_time = str(item.get("created_at_utc") or "")
        if since_value and item_time < since_value:
            continue
        filtered.append(item)
    window = filtered[-max_items:]

    label_rank = {"rejected": 0, "asserted": 1, "proven": 2}
    window_labels = [str(item.get("claim_label") or "asserted") for item in window]

    if pair_only and len(window_labels) >= 2:
        trend_labels = window_labels[-2:]
        first_rank = label_rank.get(trend_labels[0], 1)
        last_rank = label_rank.get(trend_labels[1], 1)
        trend_basis = "pair"
    elif window_labels:
        trend_labels = window_labels
        first_rank = label_rank.get(window_labels[0], 1)
        last_rank = label_rank.get(window_labels[-1], 1)
        trend_basis = "window"
    else:
        trend_labels = []
        first_rank = 1
        last_rank = 1
        trend_basis = "pair" if pair_only else "window"

    if not window:
        trend = "no_matches"
        claim: ClaimLabel = "asserted"
    elif len(trend_labels) < 2:
        trend = "insufficient_data"
        claim = "asserted"
    elif last_rank > first_rank:
        trend = "improving"
        claim = "proven"
    elif last_rank < first_rank:
        trend = "degrading"
        claim = "rejected"
    else:
        trend = "stable"
        claim = "proven" if trend_labels[-1] == "proven" else "asserted"

    if (
        trend_basis == "pair"
        and trend == "degrading"
        and trend_labels[-1] in {"proven", "asserted"}
        and any(label_rank.get(item, 1) < label_rank.get(trend_labels[-1], 1) for item in window_labels[:-2])
    ):
        trend = "recovered"
        claim = "proven" if trend_labels[-1] == "proven" else "asserted"

    drift_transitions = [
        str(item.get("claim_transition") or "")
        for item in window
        if "rejected" in str(item.get("claim_transition") or "")
    ]
    return {
        "mode": "drift-window-query",
        "index_path": str(target),
        "claim_label": claim,
        "since_utc": since_value,
        "limit": max_items,
        "entries": len(window),
        "trend": trend,
        "trend_basis": trend_basis,
        "trend_pair": trend_labels,
        "window_claims": window_labels,
        "drift_transitions": drift_transitions,
        "window": window,
    }


def snapshot_index_window_summary(index_path: Path, *, window: int = 5) -> dict[str, Any]:
    """Return compact claim-window summary for status output."""

    target = index_path.expanduser().resolve()
    if not target.exists():
        return {"exists": False, "window_size": max(1, int(window)), "entries": 0}
    items = _read_snapshot_index_entries(target)[-max(1, int(window)) :]
    claims = [str(item.get("claim_label") or "asserted") for item in items]
    rejected_count = sum(1 for item in claims if item == "rejected")
    return {
        "exists": True,
        "window_size": max(1, int(window)),
        "entries": len(items),
        "claims": claims,
        "rejected_count": rejected_count,
    }


def _artifact_presence_checks(
    *,
    proof_dir: Path,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
    index_path: Path,
) -> list[dict[str, Any]]:
    """Return read-only presence checks for governance artifacts."""

    checks: list[dict[str, Any]] = []
    for artifact, path in (
        ("proof_dir", proof_dir),
        ("ledger", ledger_path),
        ("report", report_path),
        ("snapshot", snapshot_path),
        ("snapshot_index", index_path),
    ):
        target = path.expanduser().resolve()
        exists = target.exists()
        claim: ClaimLabel = "proven" if exists else "rejected"
        entry: dict[str, Any] = {
            "artifact": artifact,
            "path": str(target),
            "exists": exists,
            "claim_label": claim,
        }
        if exists and target.is_file():
            entry["sha256"] = _sha256_file(target)
        checks.append(entry)
    plan_path = latest_plan_artifact(proof_dir.expanduser().resolve())
    checks.append(
        {
            "artifact": "latest_plan",
            "path": str(plan_path) if plan_path else "",
            "exists": plan_path is not None,
            "claim_label": "proven" if plan_path else "asserted",
            "sha256": _sha256_file(plan_path) if plan_path else "",
        }
    )
    return checks


def cross_machine_replay_status() -> dict[str, Any]:
    """Report built-in cross-machine replay scaffold state (inactive unless env set)."""

    active = os.environ.get("FORGE_CROSS_MACHINE_REPLAY_ACTIVE", "").strip() == "1"
    manifest = Path("docs/proof/bumblebee-forge/cross_machine/REPLAY_MANIFEST.json")
    template = Path("docs/proof/bumblebee-forge/cross_machine/REPLAY_MANIFEST.template.json")
    scaffold_built = template.exists()
    if active:
        operational = "active"
        claim: ClaimLabel = "asserted"
        message = "Replay env is set; run scripts/forgekeeper/cross-machine-replay and record evidence."
    else:
        operational = "inactive"
        claim = "asserted"
        message = "Cross-machine replay is built in repository but not activated."
    return {
        "scaffold_built": scaffold_built,
        "operational_status": operational,
        "activation_env": "FORGE_CROSS_MACHINE_REPLAY_ACTIVE",
        "activation_env_set": active,
        "manifest_path": str(manifest),
        "manifest_exists": manifest.exists(),
        "template_path": str(template),
        "claim_label": claim,
        "message": message,
    }


def build_verification_report(
    *,
    plan_id: str,
    proof_dir: Path,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
    index_path: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """One-click read-only verification across governance artifacts."""

    generated_at = generated_at_utc or datetime.now(UTC).isoformat()
    presence = _artifact_presence_checks(
        proof_dir=proof_dir,
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
    )
    presence_claims = [str(item["claim_label"]) for item in presence]
    trace = query_governance_trace(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
        limit=5,
    )
    reconcile = query_governance_reconciliation(
        plan_id=plan_id,
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
        limit=5,
    )
    drift = query_drift_window(index_path=index_path, limit=5)
    drift_summary = traceability_drift_summary(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
    )
    drift_count = int(reconcile.get("drift_count") or 0)
    artifact_sync_claim: ClaimLabel = (
        "proven" if drift_count == 0 and not bool(drift_summary.get("drift_detected")) else "rejected"
    )
    overall = derive_claim_status(presence_claims + [artifact_sync_claim])
    return {
        "mode": "verify",
        "plan_id": plan_id,
        "generated_at_utc": generated_at,
        "claim_label": overall,
        "safety_state": "dry_run_only",
        "presence_checks": presence,
        "artifact_sync_claim_label": artifact_sync_claim,
        "trace_claim_label": str(trace.get("claim_label") or "asserted"),
        "reconcile_claim_label": str(reconcile.get("claim_label") or "asserted"),
        "reconcile_drift_count": drift_count,
        "recommendation_claim_label": str(reconcile.get("recommendation_claim_label") or "asserted"),
        "claim_trend_claim_label": str(drift.get("claim_label") or "asserted"),
        "claim_trend": str(drift.get("trend") or ""),
        "traceability_drift": drift_summary,
        "verification_steps": [
            "py -3.12 -m forge.forgekeeper --mode observe --plan-id <id> --scope .",
            "py -3.12 -m forge.forgekeeper --mode plan --plan-id <id> --scope . --goal \"bounded map\"",
            "py -3.12 -m forge.forgekeeper --mode report --plan-id <id>",
            "py -3.12 -m forge.forgekeeper --mode snapshot --plan-id <id>",
            "py -3.12 -m forge.forgekeeper --mode snapshot-index --plan-id <id>",
            "py -3.12 -m forge.forgekeeper --mode verify --plan-id <id>",
        ],
        "proof_bundle_ref": "docs/proof/bumblebee-forge/STAGE1_PROOF_BUNDLE.md",
        "cross_machine_replay": cross_machine_replay_status(),
    }


def run_reconcile_artifacts(
    *,
    plan_id: str,
    proof_dir: Path,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
    index_path: Path,
    plan_artifact_path: Path | None = None,
    evidence_refs: list[str] | None = None,
    supersedes_snapshot_id: str = "",
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Rebuild report, snapshot, and snapshot-index in order (non-destructive refresh)."""

    generated_at = generated_at_utc or datetime.now(UTC).isoformat()
    refs = evidence_refs or []
    proof_target = proof_dir.expanduser().resolve()
    plan_path = plan_artifact_path or latest_plan_artifact(proof_target)
    if plan_path is None:
        plan_path = proof_target / "stage2_attested_plan.json"

    report = build_proof_report(
        plan_artifact_path=plan_path,
        ledger_path=ledger_path,
        evidence_refs=refs,
        generated_at_utc=generated_at,
    )
    report_target = report_path.expanduser().resolve()
    report_target.parent.mkdir(parents=True, exist_ok=True)
    report_target.write_text(_json_stable(report, pretty=True), encoding="utf-8")

    snapshot = build_snapshot_index(
        report_path=report_target,
        ledger_path=ledger_path,
        evidence_refs=refs,
        created_at_utc=generated_at,
    )
    snapshot_target = snapshot_path.expanduser().resolve()
    snapshot_target.parent.mkdir(parents=True, exist_ok=True)
    snapshot_target.write_text(_json_stable(snapshot, pretty=True), encoding="utf-8")

    index_target = index_path.expanduser().resolve()
    previous_entry = _read_last_snapshot_index_entry(index_target)
    index_record = build_snapshot_index_record(
        snapshot_path=snapshot_target,
        report_path=report_target,
        ledger_path=ledger_path,
        evidence_refs=refs,
        previous_entry=previous_entry,
        supersedes_snapshot_id=supersedes_snapshot_id,
        created_at_utc=generated_at,
    )
    append_snapshot_index_record(index_record, index_target)

    post_reconcile = query_governance_reconciliation(
        plan_id=plan_id,
        ledger_path=ledger_path,
        report_path=report_target,
        snapshot_path=snapshot_target,
        index_path=index_target,
        limit=5,
    )
    claim: ClaimLabel = "proven" if int(post_reconcile.get("drift_count") or 0) == 0 else "asserted"
    return {
        "mode": "reconcile-artifacts",
        "plan_id": plan_id,
        "generated_at_utc": generated_at,
        "claim_label": claim,
        "safety_state": "dry_run_only",
        "report_path": str(report_target),
        "report_sha256": _sha256_file(report_target),
        "snapshot_path": str(snapshot_target),
        "snapshot_sha256": _sha256_file(snapshot_target),
        "snapshot_id": str(snapshot.get("snapshot_id") or ""),
        "index_path": str(index_target),
        "index_id": str(index_record.get("index_id") or ""),
        "post_reconcile": post_reconcile,
    }


def build_bundle_export_manifest(
    *,
    plan_id: str,
    proof_dir: Path,
    ledger_path: Path,
    report_path: Path,
    snapshot_path: Path,
    index_path: Path,
    verify_report_path: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Pack verify summary and governance artifact hashes into one manifest."""

    generated_at = generated_at_utc or datetime.now(UTC).isoformat()
    verification = build_verification_report(
        plan_id=plan_id,
        proof_dir=proof_dir,
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
        generated_at_utc=generated_at,
    )
    chaos = run_chaos_checks()

    artifact_specs: list[tuple[str, Path]] = [
        ("verify_report", verify_report_path),
        ("governance_report", report_path),
        ("snapshot", snapshot_path),
        ("snapshot_index", index_path),
        ("decision_ledger", ledger_path),
    ]
    plan_path = latest_plan_artifact(proof_dir.expanduser().resolve())
    if plan_path is not None:
        artifact_specs.append(("latest_plan", plan_path))

    hash_manifest: list[dict[str, Any]] = []
    manifest_claims: list[ClaimLabel] = []
    for artifact_name, target in artifact_specs:
        resolved = target.expanduser().resolve()
        exists = resolved.exists()
        claim: ClaimLabel = "proven" if exists else "rejected"
        manifest_claims.append(claim)
        entry: dict[str, Any] = {
            "artifact": artifact_name,
            "path": str(resolved),
            "exists": exists,
            "claim_label": claim,
            "sha256": _sha256_file(resolved) if exists and resolved.is_file() else "",
        }
        hash_manifest.append(entry)

    hash_manifest = sorted(hash_manifest, key=lambda item: (str(item["artifact"]), str(item["path"])))
    overall = derive_claim_status(
        manifest_claims
        + [
            str(verification.get("claim_label") or "asserted"),
            str(chaos.get("claim_label") or "asserted"),
        ]
    )
    return {
        "manifest_version": "forgekeeper.bundle_export.v1",
        "mode": "bundle-export",
        "plan_id": plan_id,
        "generated_at_utc": generated_at,
        "claim_label": overall,
        "safety_state": "dry_run_only",
        "hash_manifest": hash_manifest,
        "verification_summary": {
            "claim_label": str(verification.get("claim_label") or "asserted"),
            "trace_claim_label": str(verification.get("trace_claim_label") or "asserted"),
            "reconcile_claim_label": str(verification.get("reconcile_claim_label") or "asserted"),
            "drift_claim_label": str(verification.get("drift_claim_label") or "asserted"),
            "cross_machine_status": str(
                (verification.get("cross_machine_replay") or {}).get("operational_status") or "inactive"
            ),
        },
        "chaos_summary": {
            "claim_label": str(chaos.get("claim_label") or "asserted"),
            "scenarios_run": int(chaos.get("scenarios_run") or 0),
            "scenarios_passed": int(chaos.get("scenarios_passed") or 0),
        },
        "proof_bundle_ref": "docs/proof/bumblebee-forge/STAGE1_PROOF_BUNDLE.md",
    }


def _chaos_scenario_missing_ledger(root: Path) -> dict[str, Any]:
    report_path = root / "report.json"
    snapshot_path = root / "snapshot.json"
    index_path = root / "index.jsonl"
    ledger_path = root / "missing_ledger.jsonl"
    report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
    snapshot_path.write_text(
        json.dumps({"claim_label": "proven", "linkage": {"report_hash": "", "ledger_hash": ""}}, sort_keys=True),
        encoding="utf-8",
    )
    trace = query_governance_trace(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
    )
    actual = str(trace.get("claim_label") or "")
    expected = "rejected"
    return {
        "scenario_id": "missing_ledger",
        "expected_claim_label": expected,
        "actual_claim_label": actual,
        "passed": actual == expected,
    }


def _chaos_scenario_corrupt_report(root: Path) -> dict[str, Any]:
    ledger_path = root / "ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    report_path = root / "report.json"
    report_path.write_text("{not-json", encoding="utf-8")
    snapshot_path = root / "snapshot.json"
    index_path = root / "index.jsonl"
    trace = query_governance_trace(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
    )
    report_claim = str((trace.get("report") or {}).get("claim_label") or "")
    expected = "rejected"
    return {
        "scenario_id": "corrupt_report_json",
        "expected_claim_label": expected,
        "actual_claim_label": report_claim,
        "passed": report_claim == expected,
    }


def _chaos_scenario_hash_drift(root: Path) -> dict[str, Any]:
    ledger_path = root / "ledger.jsonl"
    ledger_path.write_text(
        json.dumps(
            {
                "record_id": "rec-chaos",
                "recorded_at_utc": "2026-05-27T00:00:00Z",
                "mode": "judge",
                "decision": "reject",
                "claim_status": "rejected",
                "evidence_refs": [],
                "reviewer": "chaos",
                "reason": "drill",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = root / "report.json"
    report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
    snapshot_path = root / "snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "claim_label": "proven",
                "linkage": {"report_hash": "deadbeef", "ledger_hash": "cafebabe"},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    index_path = root / "index.jsonl"
    drift = traceability_drift_summary(
        ledger_path=ledger_path,
        report_path=report_path,
        snapshot_path=snapshot_path,
        index_path=index_path,
    )
    expected = "rejected"
    actual = str(drift.get("claim_label") or "")
    return {
        "scenario_id": "hash_drift_snapshot",
        "expected_claim_label": expected,
        "actual_claim_label": actual,
        "passed": actual == expected and bool(drift.get("drift_detected")),
    }


def run_chaos_checks() -> dict[str, Any]:
    """Run in-memory adversarial scenarios; never mutates repository artifacts."""

    scenarios = (
        _chaos_scenario_missing_ledger,
        _chaos_scenario_corrupt_report,
        _chaos_scenario_hash_drift,
    )
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="forgekeeper-chaos-") as temp_dir:
        root = Path(temp_dir)
        for runner in scenarios:
            results.append(runner(root))
    passed = sum(1 for item in results if item.get("passed"))
    total = len(results)
    if passed == total:
        claim: ClaimLabel = "proven"
    elif passed == 0:
        claim = "rejected"
    else:
        claim = "asserted"
    return {
        "mode": "chaos-check",
        "claim_label": claim,
        "safety_state": "dry_run_only",
        "scenarios_run": total,
        "scenarios_passed": passed,
        "results": results,
    }


def build_snapshot_index_record(
    *,
    snapshot_path: Path,
    report_path: Path,
    ledger_path: Path,
    evidence_refs: list[str],
    previous_entry: dict[str, Any] | None = None,
    supersedes_snapshot_id: str = "",
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build one snapshot-index record with claim transition metadata."""

    created_at = created_at_utc or datetime.now(UTC).isoformat()
    snapshot_target = snapshot_path.expanduser().resolve()
    report_target = report_path.expanduser().resolve()
    ledger_target = ledger_path.expanduser().resolve()

    snapshot_exists = snapshot_target.exists()
    snapshot_hash = _sha256_file(snapshot_target) if snapshot_exists else ""
    snapshot_claim: ClaimLabel = "rejected"
    snapshot_id = ""
    if snapshot_exists:
        try:
            snapshot_payload = json.loads(snapshot_target.read_text(encoding="utf-8"))
            snapshot_id = str(snapshot_payload.get("snapshot_id") or "")
            parsed_claim = str(snapshot_payload.get("claim_label") or "asserted")
            snapshot_claim = parsed_claim if parsed_claim in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            snapshot_claim = "rejected"

    report_exists = report_target.exists()
    report_hash = _sha256_file(report_target) if report_exists else ""
    report_claim: ClaimLabel = "rejected" if not report_exists else "asserted"
    if report_exists:
        try:
            report_payload = json.loads(report_target.read_text(encoding="utf-8"))
            parsed = str(report_payload.get("claim_label") or "asserted")
            report_claim = parsed if parsed in {"asserted", "proven", "rejected"} else "asserted"
        except (OSError, json.JSONDecodeError):
            report_claim = "rejected"

    ledger_info = ledger_summary(ledger_target)
    ledger_exists = bool(ledger_info.get("exists"))
    ledger_hash = _sha256_file(ledger_target) if ledger_exists else ""
    ledger_claim: ClaimLabel = "proven" if int(ledger_info.get("entries") or 0) > 0 else ("asserted" if ledger_exists else "rejected")

    evidence_items: list[dict[str, Any]] = []
    evidence_claims: list[ClaimLabel] = []
    for item in sorted({ref.strip() for ref in evidence_refs if ref.strip()}):
        target = Path(item).expanduser().resolve()
        exists = target.exists()
        claim: ClaimLabel = "proven" if exists else "rejected"
        evidence_claims.append(claim)
        evidence_items.append(
            {
                "ref": item,
                "path": str(target),
                "exists": exists,
                "claim_label": claim,
                "sha256": _sha256_file(target) if exists and target.is_file() else "",
            }
        )
    evidence_claim = derive_claim_status(evidence_claims) if evidence_claims else "asserted"

    overall = derive_claim_status([snapshot_claim, report_claim, ledger_claim, evidence_claim])
    prior_claim = str((previous_entry or {}).get("claim_label") or "origin")
    claim_transition = f"{prior_claim}->{overall}"
    inherited_supersedes = str((previous_entry or {}).get("snapshot_id") or "")
    final_supersedes = supersedes_snapshot_id.strip() or inherited_supersedes

    index_seed = _hash_text(
        _json_stable(
            {
                "created_at_utc": created_at,
                "snapshot_id": snapshot_id,
                "snapshot_sha256": snapshot_hash,
                "report_sha256": report_hash,
                "ledger_sha256": ledger_hash,
                "claim_transition": claim_transition,
                "supersedes_snapshot_id": final_supersedes,
            },
            pretty=False,
        )
    )
    return {
        "index_version": "forgekeeper.snapshot_index.v1",
        "index_id": f"snapidx-{index_seed[:16]}",
        "created_at_utc": created_at,
        "claim_label": overall,
        "claim_transition": claim_transition,
        "snapshot_id": snapshot_id,
        "snapshot_path": str(snapshot_target),
        "snapshot_sha256": snapshot_hash,
        "report_path": str(report_target),
        "report_sha256": report_hash,
        "ledger_path": str(ledger_target),
        "ledger_sha256": ledger_hash,
        "supersedes_snapshot_id": final_supersedes,
        "evidence_refs": evidence_items,
    }


def append_snapshot_index_record(record: dict[str, Any], index_path: Path) -> None:
    """Append one immutable snapshot index record to JSONL."""

    target = index_path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(_json_stable(record, pretty=False))
        handle.write("\n")


def build_proof_report(
    *,
    plan_artifact_path: Path,
    ledger_path: Path,
    evidence_refs: list[str],
    ledger_tail: int = 5,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build a non-destructive proof/export report payload."""

    normalized_time = generated_at_utc or datetime.now(UTC).isoformat()
    plan_target = plan_artifact_path.expanduser().resolve()
    ledger_target = ledger_path.expanduser().resolve()

    plan_claim: ClaimLabel = "rejected"
    plan_payload: dict[str, Any] = {}
    plan_hash = ""
    if plan_target.exists():
        try:
            plan_payload = json.loads(plan_target.read_text(encoding="utf-8"))
            plan_claim = str(plan_payload.get("claim_label") or "asserted")  # type: ignore[assignment]
            if plan_claim not in {"asserted", "proven", "rejected"}:
                plan_claim = "asserted"
            plan_hash = _sha256_file(plan_target)
        except (OSError, json.JSONDecodeError):
            plan_claim = "rejected"

    ledger_entries = read_ledger_entries(ledger_target, tail=ledger_tail)
    ledger_info = ledger_summary(ledger_target)
    ledger_claim: ClaimLabel = "proven" if bool(ledger_entries) else ("asserted" if ledger_info["exists"] else "rejected")
    ledger_hash = _sha256_file(ledger_target) if ledger_target.exists() else ""

    evidence_records: list[dict[str, Any]] = []
    evidence_statuses: list[ClaimLabel] = []
    for item in sorted({ref.strip() for ref in evidence_refs if ref.strip()}):
        target = Path(item).expanduser().resolve()
        exists = target.exists()
        status: ClaimLabel = "proven" if exists else "rejected"
        evidence_statuses.append(status)
        evidence_records.append(
            {
                "ref": item,
                "path": str(target),
                "exists": exists,
                "claim_label": status,
                "sha256": _sha256_file(target) if exists and target.is_file() else "",
            }
        )
    evidence_claim = derive_claim_status(evidence_statuses) if evidence_statuses else "asserted"

    overall = derive_claim_status([plan_claim, ledger_claim, evidence_claim])
    hash_manifest = [
        {
            "artifact": "plan_artifact",
            "path": str(plan_target),
            "sha256": plan_hash,
            "exists": plan_target.exists(),
        },
        {
            "artifact": "decision_ledger",
            "path": str(ledger_target),
            "sha256": ledger_hash,
            "exists": ledger_target.exists(),
        },
    ] + [
        {
            "artifact": "evidence_ref",
            "path": item["path"],
            "sha256": item["sha256"],
            "exists": item["exists"],
        }
        for item in evidence_records
    ]
    hash_manifest = sorted(hash_manifest, key=lambda item: (str(item["artifact"]), str(item["path"])))
    return {
        "report_version": "forgekeeper.proof_report.v1",
        "generated_at_utc": normalized_time,
        "claim_label": overall,
        "safety_state": "dry_run_only",
        "plan_artifact": {
            "path": str(plan_target),
            "exists": plan_target.exists(),
            "claim_label": plan_claim,
            "deterministic_seed": plan_payload.get("deterministic_seed", ""),
            "rollback_token": plan_payload.get("rollback_token", ""),
            "attestation_overall": plan_payload.get("attestation_overall", ""),
            "sha256": plan_hash,
        },
        "ledger": {
            "path": str(ledger_target),
            "claim_label": ledger_claim,
            "summary": ledger_info,
            "tail_entries": ledger_entries,
            "sha256": ledger_hash,
        },
        "evidence_refs": {
            "claim_label": evidence_claim,
            "items": evidence_records,
        },
        "hash_manifest": hash_manifest,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Forgekeeper Stage 1/2 dry-run CLI.")
    parser.add_argument(
        "--mode",
        choices=sorted(ALLOWED_MODES),
        default="observe",
        help="operation mode; all modes are non-destructive",
    )
    parser.add_argument("--plan-id", required=True, help="plan identifier")
    parser.add_argument("--goal", default="", help="goal statement")
    parser.add_argument("--scope", default=".", help="target scope")
    parser.add_argument(
        "--focus-file",
        action="append",
        default=[],
        help="focused file path (repeatable)",
    )
    parser.add_argument(
        "--constraints-json",
        default="{}",
        help="json object of request constraints",
    )
    parser.add_argument(
        "--proof-bundle-ref",
        default="",
        help="explicit proof bundle reference for attestation checks",
    )
    parser.add_argument(
        "--context-file",
        action="append",
        default=[],
        help="context mapping as path=content",
    )
    parser.add_argument(
        "--decision",
        choices=["approve", "reject"],
        default="reject",
        help="judge decision (judge mode only)",
    )
    parser.add_argument("--reason", default="", help="judge reason")
    parser.add_argument("--reviewer", default="", help="judge reviewer identity")
    parser.add_argument(
        "--allow-approve",
        action="store_true",
        help="explicitly allow approve in judge mode",
    )
    parser.add_argument(
        "--allow-apply",
        action="store_true",
        help="unsafe placeholder flag (always blocked in stage 1/2)",
    )
    parser.add_argument(
        "--output",
        default="json",
        choices=["json", "text"],
        help="output format",
    )
    parser.add_argument(
        "--write-plan",
        default="",
        help="optional file path to persist plan json (plan mode only)",
    )
    parser.add_argument(
        "--ledger-path",
        default=".runtime/forgekeeper/decision_ledger.jsonl",
        help="append-only decision ledger path",
    )
    parser.add_argument(
        "--evidence-ref",
        action="append",
        default=[],
        help="evidence reference path or identifier (repeatable)",
    )
    parser.add_argument(
        "--proof-dir",
        default="docs/proof/bumblebee-forge",
        help="proof artifact directory for report mode",
    )
    parser.add_argument(
        "--plan-artifact",
        default="",
        help="plan artifact path for report mode (auto-discover if empty)",
    )
    parser.add_argument(
        "--report-path",
        default="docs/proof/bumblebee-forge/forgekeeper_report.json",
        help="report output path for report mode",
    )
    parser.add_argument(
        "--write-report",
        nargs="?",
        const="docs/proof/bumblebee-forge/forgekeeper_verify_report.json",
        default="",
        help="verify mode: write verification json (optional path; default proof bundle path)",
    )
    parser.add_argument(
        "--verify-report-path",
        default="docs/proof/bumblebee-forge/forgekeeper_verify_report.json",
        help="verify report path for bundle-export mode",
    )
    parser.add_argument(
        "--write-bundle-export",
        nargs="?",
        const="docs/proof/bumblebee-forge/forgekeeper_bundle_manifest.json",
        default="",
        help="bundle-export mode: write consolidated manifest json (optional path)",
    )
    parser.add_argument(
        "--ledger-tail",
        default=5,
        type=int,
        help="number of latest ledger entries to include in report mode",
    )
    parser.add_argument(
        "--fixed-timestamp",
        default="",
        help="fixed UTC timestamp for deterministic report generation",
    )
    parser.add_argument(
        "--snapshot-path",
        default="docs/proof/bumblebee-forge/forgekeeper_snapshot.json",
        help="snapshot output path for snapshot mode",
    )
    parser.add_argument(
        "--snapshot-index-path",
        default="docs/proof/bumblebee-forge/forgekeeper_snapshot_index.jsonl",
        help="append-only snapshot index jsonl path",
    )
    parser.add_argument(
        "--supersedes-snapshot-id",
        default="",
        help="explicit superseded snapshot id for snapshot-index mode",
    )
    parser.add_argument(
        "--query-snapshot-id",
        default="",
        help="snapshot id filter for snapshot-query mode",
    )
    parser.add_argument(
        "--query-claim-label",
        default="",
        help="claim label filter for snapshot-query mode",
    )
    parser.add_argument(
        "--query-since-utc",
        default="",
        help="created_at lower bound for snapshot-query mode",
    )
    parser.add_argument(
        "--query-limit",
        default=20,
        type=int,
        help="max records returned for snapshot-query mode",
    )
    parser.add_argument(
        "--query-ledger-claim-status",
        default="",
        help="ledger claim_status filter for trace-query mode",
    )
    parser.add_argument(
        "--query-reviewer",
        default="",
        help="reviewer filter for trace-query mode",
    )
    return parser


def _parse_context_map(raw_items: list[str]) -> dict[str, str]:
    context: dict[str, str] = {}
    for item in raw_items:
        left, sep, right = item.partition("=")
        if not sep or not left.strip():
            raise ForgekeeperError("context mapping must be path=content.")
        context[left.strip()] = right
    return context


def _print_payload(payload: dict[str, Any], output: str) -> None:
    if output == "text":
        for key in sorted(payload.keys()):
            print(f"{key}: {payload[key]}")
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def _json_stable(payload: dict[str, Any], *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(payload, indent=2, sort_keys=True)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def run_cli(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _enforce_non_destructive(args.mode, args.allow_apply)

    try:
        constraints = json.loads(args.constraints_json)
    except json.JSONDecodeError as exc:
        raise ForgekeeperError("constraints-json must be valid json object.") from exc
    if not isinstance(constraints, dict):
        raise ForgekeeperError("constraints-json must decode to an object.")
    if str(args.proof_bundle_ref).strip():
        constraints["proof_bundle_ref"] = str(args.proof_bundle_ref).strip()

    request = ForgekeeperRequest(
        plan_id=args.plan_id.strip(),
        goal=args.goal.strip(),
        scope=args.scope.strip() or ".",
        focus_files=[str(item) for item in args.focus_file],
        constraints=constraints,
        context_files=_parse_context_map([str(item) for item in args.context_file]),
    )

    if args.mode == "observe":
        payload = observe_request(request)
        _print_payload(payload, args.output)
        return 0

    if args.mode == "judge":
        result = judge_request(
            request,
            decision=args.decision,
            reason=args.reason,
            reviewer=args.reviewer,
            allow_approve=bool(args.allow_approve),
        )
        record = build_decision_record(result)
        record.evidence_refs = [str(item).strip() for item in args.evidence_ref if str(item).strip()]
        append_decision_record(record, Path(args.ledger_path))
        payload = result.model_dump()
        payload["decision_record"] = record.model_dump()
        payload["ledger_path"] = str(Path(args.ledger_path).expanduser().resolve())
        payload["ledger_appended"] = True
        _print_payload(payload, args.output)
        return 0

    if args.mode == "plan":
        plan = build_dry_run_plan(request, mode="plan")
        payload = plan.model_dump()
        if args.write_plan.strip():
            target = Path(args.write_plan).expanduser().resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        _print_payload(payload, args.output)
        return 0

    if args.mode == "report":
        proof_dir = Path(args.proof_dir)
        plan_path = Path(args.plan_artifact) if str(args.plan_artifact).strip() else latest_plan_artifact(proof_dir)
        if plan_path is None:
            plan_path = proof_dir / "missing-plan-artifact.json"
        generated_at = str(args.fixed_timestamp).strip() or None
        report = build_proof_report(
            plan_artifact_path=plan_path,
            ledger_path=Path(args.ledger_path),
            evidence_refs=[str(item).strip() for item in args.evidence_ref if str(item).strip()],
            ledger_tail=max(1, int(args.ledger_tail)),
            generated_at_utc=generated_at,
        )
        target = Path(args.report_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_json_stable(report, pretty=True), encoding="utf-8")
        report["report_path"] = str(target)
        _print_payload(report, args.output)
        return 0

    if args.mode == "snapshot":
        created_at = str(args.fixed_timestamp).strip() or None
        snapshot = build_snapshot_index(
            report_path=Path(args.report_path),
            ledger_path=Path(args.ledger_path),
            evidence_refs=[str(item).strip() for item in args.evidence_ref if str(item).strip()],
            created_at_utc=created_at,
        )
        target = Path(args.snapshot_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_json_stable(snapshot, pretty=True), encoding="utf-8")
        snapshot["snapshot_path"] = str(target)
        _print_payload(snapshot, args.output)
        return 0

    if args.mode == "snapshot-index":
        created_at = str(args.fixed_timestamp).strip() or None
        index_path = Path(args.snapshot_index_path)
        previous_entry = _read_last_snapshot_index_entry(index_path)
        record = build_snapshot_index_record(
            snapshot_path=Path(args.snapshot_path),
            report_path=Path(args.report_path),
            ledger_path=Path(args.ledger_path),
            evidence_refs=[str(item).strip() for item in args.evidence_ref if str(item).strip()],
            previous_entry=previous_entry,
            supersedes_snapshot_id=str(args.supersedes_snapshot_id),
            created_at_utc=created_at,
        )
        append_snapshot_index_record(record, index_path)
        payload = {
            "mode": "snapshot-index",
            "index_path": str(index_path.expanduser().resolve()),
            "index_appended": True,
            "record": record,
            "index_summary": snapshot_index_summary(index_path),
        }
        _print_payload(payload, args.output)
        return 0

    if args.mode == "snapshot-query":
        index_path = Path(args.snapshot_index_path)
        payload = query_snapshot_index(
            index_path=index_path,
            snapshot_id=str(args.query_snapshot_id),
            claim_label=str(args.query_claim_label),
            since_utc=str(args.query_since_utc),
            limit=max(1, int(args.query_limit)),
        )
        if index_path.expanduser().resolve().exists():
            payload["snapshot_index_sha256"] = _sha256_file(index_path.expanduser().resolve())
        _print_payload(payload, args.output)
        return 0

    if args.mode == "trace-query":
        payload = query_governance_trace(
            ledger_path=Path(args.ledger_path),
            report_path=Path(args.report_path),
            snapshot_path=Path(args.snapshot_path),
            index_path=Path(args.snapshot_index_path),
            ledger_claim_status=str(args.query_ledger_claim_status),
            reviewer=str(args.query_reviewer),
            since_utc=str(args.query_since_utc),
            limit=max(1, int(args.query_limit)),
        )
        _print_payload(payload, args.output)
        return 0

    if args.mode == "reconcile-query":
        payload = query_governance_reconciliation(
            plan_id=request.plan_id,
            ledger_path=Path(args.ledger_path),
            report_path=Path(args.report_path),
            snapshot_path=Path(args.snapshot_path),
            index_path=Path(args.snapshot_index_path),
            ledger_claim_status=str(args.query_ledger_claim_status),
            reviewer=str(args.query_reviewer),
            since_utc=str(args.query_since_utc),
            limit=max(1, int(args.query_limit)),
        )
        _print_payload(payload, args.output)
        return 0

    if args.mode == "drift-window-query":
        payload = query_drift_window(
            index_path=Path(args.snapshot_index_path),
            since_utc=str(args.query_since_utc),
            limit=max(1, int(args.query_limit)),
        )
        _print_payload(payload, args.output)
        return 0

    if args.mode == "verify":
        generated_at = str(args.fixed_timestamp).strip() or None
        payload = build_verification_report(
            plan_id=request.plan_id,
            proof_dir=Path(args.proof_dir),
            ledger_path=Path(args.ledger_path),
            report_path=Path(args.report_path),
            snapshot_path=Path(args.snapshot_path),
            index_path=Path(args.snapshot_index_path),
            generated_at_utc=generated_at,
        )
        write_path = str(args.write_report).strip()
        if write_path:
            target = Path(write_path).expanduser().resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_json_stable(payload, pretty=True), encoding="utf-8")
            payload["verify_report_path"] = str(target)
            payload["verify_report_sha256"] = _sha256_file(target)
        _print_payload(payload, args.output)
        return 0

    if args.mode == "chaos-check":
        payload = run_chaos_checks()
        _print_payload(payload, args.output)
        return 0

    if args.mode == "reconcile-artifacts":
        generated_at = str(args.fixed_timestamp).strip() or None
        plan_path = Path(args.plan_artifact) if str(args.plan_artifact).strip() else None
        payload = run_reconcile_artifacts(
            plan_id=request.plan_id,
            proof_dir=Path(args.proof_dir),
            ledger_path=Path(args.ledger_path),
            report_path=Path(args.report_path),
            snapshot_path=Path(args.snapshot_path),
            index_path=Path(args.snapshot_index_path),
            plan_artifact_path=plan_path,
            evidence_refs=[str(item).strip() for item in args.evidence_ref if str(item).strip()],
            supersedes_snapshot_id=str(args.supersedes_snapshot_id),
            generated_at_utc=generated_at,
        )
        _print_payload(payload, args.output)
        return 0

    if args.mode == "bundle-export":
        generated_at = str(args.fixed_timestamp).strip() or None
        verify_path = Path(args.verify_report_path)
        payload = build_bundle_export_manifest(
            plan_id=request.plan_id,
            proof_dir=Path(args.proof_dir),
            ledger_path=Path(args.ledger_path),
            report_path=Path(args.report_path),
            snapshot_path=Path(args.snapshot_path),
            index_path=Path(args.snapshot_index_path),
            verify_report_path=verify_path,
            generated_at_utc=generated_at,
        )
        write_path = str(args.write_bundle_export).strip()
        if write_path:
            target = Path(write_path).expanduser().resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_json_stable(payload, pretty=True), encoding="utf-8")
            payload["bundle_export_path"] = str(target)
            payload["bundle_export_sha256"] = _sha256_file(target)
        _print_payload(payload, args.output)
        return 0

    payload = {
        "plan_id": request.plan_id,
        "mode": "status",
        "claim_label": "asserted",
        "safety_state": "dry_run_only",
        "goal": request.goal,
        "scope": request.scope,
        "ledger": ledger_summary(Path(args.ledger_path)),
        "report_path": str(Path(args.report_path).expanduser().resolve()),
        "snapshot_path": str(Path(args.snapshot_path).expanduser().resolve()),
        "snapshot_index_path": str(Path(args.snapshot_index_path).expanduser().resolve()),
    }
    report_file = Path(args.report_path).expanduser().resolve()
    if report_file.exists():
        payload["report_sha256"] = _sha256_file(report_file)
        try:
            report_payload = json.loads(report_file.read_text(encoding="utf-8"))
            payload["report_claim_label"] = str(report_payload.get("claim_label") or "asserted")
        except (OSError, json.JSONDecodeError):
            payload["report_claim_label"] = "rejected"
    snapshot_file = Path(args.snapshot_path).expanduser().resolve()
    if snapshot_file.exists():
        payload["snapshot_sha256"] = _sha256_file(snapshot_file)
        try:
            snapshot_payload = json.loads(snapshot_file.read_text(encoding="utf-8"))
            payload["snapshot_claim_label"] = str(snapshot_payload.get("claim_label") or "asserted")
            payload["snapshot_id"] = str(snapshot_payload.get("snapshot_id") or "")
        except (OSError, json.JSONDecodeError):
            payload["snapshot_claim_label"] = "rejected"
    index_file = Path(args.snapshot_index_path).expanduser().resolve()
    payload["snapshot_index"] = snapshot_index_summary(index_file)
    if index_file.exists():
        payload["snapshot_index_sha256"] = _sha256_file(index_file)
        recent = _read_snapshot_index_entries(index_file)[-3:]
        payload["snapshot_index_recent"] = [
            {
                "index_id": str(item.get("index_id") or ""),
                "snapshot_id": str(item.get("snapshot_id") or ""),
                "claim_transition": str(item.get("claim_transition") or ""),
            }
            for item in recent
        ]
    payload["snapshot_index_window"] = snapshot_index_window_summary(index_file, window=5)
    payload["traceability"] = {
        "report_exists": report_file.exists(),
        "snapshot_exists": snapshot_file.exists(),
        "snapshot_index_exists": index_file.exists(),
        "ledger_exists": bool(payload["ledger"].get("exists")),
    }
    payload["traceability_drift"] = traceability_drift_summary(
        ledger_path=Path(args.ledger_path),
        report_path=Path(args.report_path),
        snapshot_path=Path(args.snapshot_path),
        index_path=Path(args.snapshot_index_path),
    )
    verify_report_file = Path(
        str(args.write_report).strip() or "docs/proof/bumblebee-forge/forgekeeper_verify_report.json"
    ).expanduser().resolve()
    if args.mode == "status" and verify_report_file.exists():
        payload["verify_report_path"] = str(verify_report_file)
        payload["verify_report_sha256"] = _sha256_file(verify_report_file)
        try:
            verify_payload = json.loads(verify_report_file.read_text(encoding="utf-8"))
            payload["verify_report_claim_label"] = str(verify_payload.get("claim_label") or "asserted")
        except (OSError, json.JSONDecodeError):
            payload["verify_report_claim_label"] = "rejected"
    payload["verification"] = build_verification_report(
        plan_id=request.plan_id,
        proof_dir=Path(args.proof_dir),
        ledger_path=Path(args.ledger_path),
        report_path=Path(args.report_path),
        snapshot_path=Path(args.snapshot_path),
        index_path=Path(args.snapshot_index_path),
    )
    _print_payload(payload, args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run_cli(argv)
    except ForgekeeperError as exc:
        print(f"forgekeeper_error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
