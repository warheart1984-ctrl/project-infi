"""Governed Composite Mission — URG atomic unit M and signed mission receipt."""

from __future__ import annotations

from hashlib import sha256
import json
import os
import time
from typing import Any

from src.ugr.mission.provider_organ import ProviderOrgan, ProviderOrganRegistry


URG_GCM_VERSION = "1.9"
CLOUD_INVARIANT_FAMILIES = (
    "cloud_identity",
    "cloud_boundary",
    "cloud_tenant_boundary",
    "cloud_tenant_federation",
    "cloud_federation_governance",
    "cloud_continuity",
    "cloud_causality",
    "cloud_contract",
    "cloud_budget",
    "cloud_mutation",
    "cloud_execution_safety",
    "cloud_composite",
)
URG_GCM_PHASES = ("decompose", "assign", "enforce", "receipt")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def build_goal(request: dict[str, Any]) -> dict[str, Any]:
    """Goal G — intent, objective, operator context."""
    return {
        "mission_kind": str(request.get("mission_kind") or "").strip(),
        "intent": str(request.get("intent") or "general_qa").strip().lower(),
        "objective": str(request.get("objective") or "").strip(),
        "operator_id": str(request.get("operator_id") or "").strip(),
        "tenant_id": str(request.get("tenant_id") or "global").strip() or "global",
        "aais_instance_id": str(request.get("aais_instance_id") or "").strip(),
        "region_id": str(request.get("region_id") or "").strip(),
    }


def build_constraints(request: dict[str, Any]) -> dict[str, Any]:
    """Constraints C — mission-level law envelope."""
    raw = dict(request.get("constraints") or {})
    context = dict(request.get("context") or {})
    return {
        **raw,
        "halt_on_failure": bool(request.get("halt_on_failure", True)),
        "forbid_express": bool(context.get("forbid_express")),
        "context": context,
    }


def decompose_mission(request: dict[str, Any]) -> dict[str, Any]:
    """Phase 1 — break mission into ordered sub-goals (steps)."""
    steps = []
    for ordinal, step in enumerate(list(request.get("steps") or []), start=1):
        step = dict(step)
        steps.append(
            {
                "ordinal": ordinal,
                "step_id": str(step.get("step_id") or f"step-{ordinal}").strip(),
                "sub_goal": str(step.get("objective") or step.get("sub_goal") or "").strip(),
                "requested_organ_id": str(step.get("organ_id") or "").strip(),
                "aais_instance_id": str(step.get("aais_instance_id") or request.get("aais_instance_id") or "").strip(),
            }
        )
    return {
        "phase": "decompose",
        "step_count": len(steps),
        "decomposition": steps,
        "law": "urg_decompose_mission",
    }


def assign_organs(
    decomposition: dict[str, Any],
    *,
    organ_registry: ProviderOrganRegistry,
    auto_assign_meta: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Phase 2 — bind each sub-goal to a participating organ (and optional AAIS instance)."""
    assignments: list[dict[str, Any]] = []
    participating: list[dict[str, Any]] = []
    seen_organs: set[str] = set()
    meta_by_step = {str(m.get("step_id") or ""): m for m in (auto_assign_meta or [])}

    for item in list(decomposition.get("decomposition") or []):
        organ_id = str(item.get("requested_organ_id") or "").strip()
        organ = organ_registry.get(organ_id)
        step_id = str(item.get("step_id") or "")
        match = dict(meta_by_step.get(step_id) or {})
        entry = {
            "step_id": item.get("step_id"),
            "ordinal": item.get("ordinal"),
            "organ_id": organ_id,
            "aais_instance_id": item.get("aais_instance_id"),
            "assigned": organ is not None,
            "provider": organ.provider if organ else None,
            "tier": organ.tier if organ else None,
            "auto_assigned": bool(match.get("auto_assigned")),
            "match_reason": str(match.get("match_reason") or ("explicit_organ_id" if organ_id else "")),
        }
        assignments.append(entry)
        if organ and organ_id not in seen_organs:
            seen_organs.add(organ_id)
            participating.append(
                {
                    "organ_id": organ.organ_id,
                    "provider": organ.provider,
                    "tier": organ.tier,
                    "contract": dict(organ.contract),
                    "aais_instances": sorted(
                        {
                            str(a.get("aais_instance_id") or "")
                            for a in decomposition.get("decomposition") or []
                            if str(a.get("requested_organ_id") or "") == organ_id and a.get("aais_instance_id")
                        }
                        | {str(item.get("aais_instance_id") or "")}
                        - {""}
                    ),
                }
            )

    return {
        "phase": "assign",
        "assignments": assignments,
        "participating_organs": participating,
        "auto_assign_meta": list(auto_assign_meta or []),
        "law": "urg_assign_organs",
    }


def build_invariant_set(
    *,
    mission_open: list[dict[str, Any]],
    step_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Invariant set I — cloud families + per-step outcomes."""
    per_step = []
    for step in step_results:
        per_step.append(
            {
                "step_id": step.get("step_id"),
                "action_id": step.get("action_id"),
                "results": list(step.get("invariant_results") or []),
                "passed": not any(
                    r.get("status") == "hard_fail" for r in (step.get("invariant_results") or [])
                ),
            }
        )
    return {
        "families": list(CLOUD_INVARIANT_FAMILIES),
        "mission_open": list(mission_open),
        "per_step": per_step,
        "all_passed": all(item.get("passed", False) for item in per_step) if per_step else True,
    }


def build_ledger_trail(
    *,
    mission_id: str,
    ledger_refs: list[str],
    ledger_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Ledger trail L — forensic action chain."""
    rows = list(ledger_rows or [])
    return {
        "mission_id": mission_id,
        "action_ids": list(ledger_refs),
        "entry_count": len(rows),
        "entries": rows,
        "causality_chain": [row.get("action_id") for row in rows],
    }


def _participating_aais_instances(assignment: dict[str, Any]) -> list[str]:
    instances: set[str] = set()
    for item in list(assignment.get("assignments") or []):
        aid = str(item.get("aais_instance_id") or "").strip()
        if aid:
            instances.add(aid)
    return sorted(instances)


def build_governed_composite_mission(
    *,
    mission_id: str,
    request: dict[str, Any],
    ingress: dict[str, Any],
    decomposition: dict[str, Any],
    assignment: dict[str, Any],
    invariant_set: dict[str, Any],
    ledger_trail: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    """
    M = (Goal, Constraints, Participating Organs, Invariant Set, Ledger Trail)

    URG atomic unit: Governed Composite Mission.
    """
    return {
        "gcm_version": URG_GCM_VERSION,
        "mission_id": mission_id,
        "atomic_unit": "governed_composite_mission",
        "goal": build_goal(request),
        "constraints": build_constraints(request),
        "participating_organs": list(assignment.get("participating_organs") or []),
        "participating_aais_instances": _participating_aais_instances(assignment),
        "invariant_set": invariant_set,
        "ledger_trail": ledger_trail,
        "ingress": dict(ingress),
        "status": status,
        "phases_completed": list(URG_GCM_PHASES) if status == "ok" else ["decompose", "assign", "enforce"],
    }


def _collect_aais_step_summaries(steps: list[dict[str, Any]]) -> list[str]:
    summaries: list[str] = []
    for step in steps:
        deliberation = dict(step.get("aais_deliberation") or {})
        summary = str(deliberation.get("summary") or step.get("step_id") or "")
        if summary:
            summaries.append(summary[:200])
    return summaries


def issue_mission_receipt(
    gcm: dict[str, Any],
    *,
    ingress: dict[str, Any],
    enforcement_summary: str,
    aais_step_summaries: list[str] | None = None,
    runtime_dir: str | None = None,
    ledger_rows: list[dict[str, Any]] | None = None,
    block_context: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
    steps: list[dict[str, Any]] | None = None,
    rail: str = "NORMAL",
    federation_context: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Phase 4 — legacy flat receipt + MissionReceipt schema v1."""
    from src.ugr.mission.mission_receipt import build_mission_receipt_v2
    from src.ugr.mission.receipt_signing import (
        build_receipt_canonical_payload,
        sign_mission_receipt_v2,
        sign_receipt_payload,
    )

    goal = dict(gcm.get("goal") or {})
    operator_id = str(goal.get("operator_id") or ingress.get("operator_id") or "default")
    canonical_payload = build_receipt_canonical_payload(
        gcm,
        ingress=ingress,
        aais_step_summaries=aais_step_summaries,
    )
    signed = sign_receipt_payload(
        canonical_payload,
        operator_id=operator_id,
        runtime_dir=runtime_dir,
        create_key_if_missing=True,
    )
    legacy = {
        "receipt_version": URG_GCM_VERSION,
        "mission_id": gcm.get("mission_id"),
        "issued_at": int(time.time()),
        "status": gcm.get("status"),
        "enforcement_summary": enforcement_summary,
        "content_digest": signed["content_digest"],
        "receipt_mac": signed.get("receipt_mac"),
        "receipt_signature": signed["receipt_signature"],
        "receipt_algorithm": signed["receipt_algorithm"],
        "operator_id": signed["operator_id"],
        "ingress_stamp_hash": ingress.get("stamp_hash"),
        "forensic": {
            "ledger_entry_count": (gcm.get("ledger_trail") or {}).get("entry_count", 0),
            "participating_organ_count": len(gcm.get("participating_organs") or []),
            "invariant_families": (gcm.get("invariant_set") or {}).get("families"),
        },
        "law": "urg_signed_mission_receipt",
    }

    from src.ugr.invariants.cloud_invariants import check_cloud_causality, has_hard_fail

    mission_id = str(gcm.get("mission_id") or "")
    step_list = list(steps or [])
    mission_kind = str((request or {}).get("mission_kind") or (gcm.get("goal") or {}).get("mission_kind") or "")
    if str(gcm.get("status") or "") == "ok" and mission_kind != "governance_mutation":
        causality = check_cloud_causality(
            list(ledger_rows or []),
            step_list,
            mission_id=mission_id,
        )
        if has_hard_fail(causality):
            raise ReceiptBuildError(causality[0].get("details", "cloud_causality_failed"))

    req = dict(request or {})
    from src.ugr.mission.execution_policy import is_shadow_execution, resolve_execution_mode

    exec_mode = resolve_execution_mode(req)
    from src.ugr.platform.tenant_registry import normalize_tenant_id

    store_root = runtime_dir or os.getenv("AAIS_RUNTIME_DIR")
    tenant_norm = normalize_tenant_id(
        ingress.get("tenant_id") or (request or {}).get("tenant_id") or "global"
    )
    fed_ingress = dict(ingress)
    if federation_context and store_root:
        from pathlib import Path

        from src.ugr.mission.mission_receipt import build_federation_receipt_fields

        digest, cref = build_federation_receipt_fields(
            runtime_dir=Path(store_root),
            home_tenant_id=tenant_norm,
            mission_id=str(gcm.get("mission_id") or ""),
            federation_context=list(federation_context),
        )
        if digest:
            fed_ingress["federation_digest"] = digest
        if cref:
            fed_ingress["counterparty_receipt_ref"] = cref
    schema_body = build_mission_receipt_v2(
        gcm=gcm,
        ingress=fed_ingress,
        ledger_rows=list(ledger_rows or []),
        block_context=block_context,
        request=request,
        rail=rail,
        execution_mode=exec_mode,
        shadow=is_shadow_execution(exec_mode) if exec_mode else None,
    )
    schema_signed = sign_mission_receipt_v2(
        schema_body,
        operator_id=operator_id,
        runtime_dir=runtime_dir,
        create_keys_if_missing=True,
    )
    from src.ugr.mission.mission_receipt_store import MissionReceiptStore

    store = MissionReceiptStore(runtime_dir=store_root, tenant_id=tenant_norm)
    store.persist_receipt(
        str(gcm.get("mission_id") or ""),
        legacy=legacy,
        schema=schema_signed,
        tenant_id=tenant_norm,
    )
    if federation_context and fed_ingress.get("counterparty_receipt_ref"):
        peer_tenant = normalize_tenant_id(
            str(federation_context[0].get("peer_tenant") or "")
        )
        store.persist_federation_counterparty_stub(
            str(gcm.get("mission_id") or ""),
            home_tenant_id=tenant_norm,
            peer_tenant_id=peer_tenant,
            home_receipt_schema=schema_signed,
            counterparty_receipt_ref=dict(fed_ingress.get("counterparty_receipt_ref") or {}),
            federation_digest=str(fed_ingress.get("federation_digest") or ""),
        )
    return legacy, schema_signed


class ReceiptBuildError(RuntimeError):
    """Mission receipt cannot be issued (cloud causality / invariant proof failed)."""


def attach_gcm_to_response(
    response: dict[str, Any],
    *,
    request: dict[str, Any],
    ingress: dict[str, Any],
    decomposition: dict[str, Any],
    assignment: dict[str, Any],
    mission_open: list[dict[str, Any]],
    ledger_rows: list[dict[str, Any]] | None = None,
    block_context: dict[str, Any] | None = None,
    steps: list[dict[str, Any]] | None = None,
    rail: str = "NORMAL",
    runtime_dir: str | None = None,
    federation_context: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Attach GCM tuple and signed receipt to a mission runtime response."""
    mission_id = str(response.get("mission_id") or ingress.get("mission_id") or "")
    invariant_set = build_invariant_set(
        mission_open=mission_open,
        step_results=list(response.get("steps") or []),
    )
    ledger_trail = build_ledger_trail(
        mission_id=mission_id,
        ledger_refs=list(response.get("ledger_refs") or []),
        ledger_rows=ledger_rows,
    )
    req = dict(request)
    if str(req.get("mission_kind") or ""):
        req.setdefault("intent", str(req.get("mission_kind")))
    gcm = build_governed_composite_mission(
        mission_id=mission_id,
        request=req,
        ingress=ingress,
        decomposition=decomposition,
        assignment=assignment,
        invariant_set=invariant_set,
        ledger_trail=ledger_trail,
        status=str(response.get("status") or "unknown"),
    )
    import os

    resolved_runtime = runtime_dir
    if not resolved_runtime:
        configured = os.getenv("AAIS_RUNTIME_DIR")
        if configured:
            resolved_runtime = configured
    step_list = list(steps or response.get("steps") or [])
    legacy_receipt, schema_receipt = issue_mission_receipt(
        gcm,
        ingress=ingress,
        enforcement_summary=str(response.get("summary") or ""),
        aais_step_summaries=_collect_aais_step_summaries(step_list),
        runtime_dir=resolved_runtime,
        ledger_rows=ledger_rows,
        block_context=block_context,
        request=request,
        steps=step_list,
        rail=rail,
        federation_context=federation_context,
    )
    updated = dict(response)
    updated["governed_composite_mission"] = gcm
    updated["mission_receipt"] = legacy_receipt
    updated["mission_receipt_schema"] = schema_receipt
    updated["urg_phases"] = {
        "decompose": decomposition,
        "assign": assignment,
        "enforce": {
            "phase": "enforce",
            "cloud_invariants": response.get("cloud_invariants"),
            "steps": response.get("steps"),
        },
        "receipt": legacy_receipt,
        "receipt_schema": schema_receipt,
    }
    updated["switchboard"] = dict(updated.get("switchboard") or {})
    updated["switchboard"]["atomic_unit"] = "governed_composite_mission"
    if str(response.get("status") or "") == "ok":
        from src.ugr.mission.organ_trust import update_trust_from_receipt
        from src.ugr.platform.tenant_registry import normalize_tenant_id

        update_trust_from_receipt(
            schema_receipt,
            steps=step_list,
            tenant_id=normalize_tenant_id(ingress.get("tenant_id") or "global"),
        )
    return updated
