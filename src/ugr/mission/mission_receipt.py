"""MissionReceipt v1 schema builders."""

from __future__ import annotations

from hashlib import sha256
import json
import time
from pathlib import Path
from typing import Any, Union

from src.ugr.invariants.cloud_manifold import CLOUD_INVARIANT_SET_VERSION
from src.ugr.mission.ledger_merkle import compute_ledger_merkle_root


MISSION_RECEIPT_SCHEMA_VERSION = "1.3"
OUTCOME_COMPLETED = "completed"
OUTCOME_FAILED = "failed"
OUTCOME_VETOED = "vetoed"

FAILURE_REASON_UNFULFILLABLE_CONSTRAINTS = "UNFULFILLABLE_CONSTRAINTS"
FAILURE_REASON_NO_ADMISSIBLE_ORGAN = "NO_ADMISSIBLE_ORGAN"
FAILURE_REASON_GATE_REJECTION = "GATE_REJECTION"
FAILURE_REASON_OPERATOR_VETO = "OPERATOR_VETO"
FAILURE_REASON_RUNTIME_ERROR = "RUNTIME_ERROR"
FAILURE_REASON_BUDGET_EXCEEDED = "BUDGET_EXCEEDED"

FAILURE_REASONS = (
    FAILURE_REASON_UNFULFILLABLE_CONSTRAINTS,
    FAILURE_REASON_NO_ADMISSIBLE_ORGAN,
    FAILURE_REASON_GATE_REJECTION,
    FAILURE_REASON_OPERATOR_VETO,
    FAILURE_REASON_RUNTIME_ERROR,
    FAILURE_REASON_BUDGET_EXCEEDED,
)

DEFAULT_ORGAN_REGISTRY_VERSION = "1.0"
CONSTRAINT_INVARIANT_FAMILIES = frozenset(
    {
        "cloud_boundary",
        "cloud_identity",
        "cloud_composite",
        "cloud_causality",
        "cloud_continuity",
        "cloud_contract",
    }
)


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _default_organs_registry_version() -> str:
    path = Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "provider-organs.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        return str(payload.get("registry_version") or DEFAULT_ORGAN_REGISTRY_VERSION)
    return DEFAULT_ORGAN_REGISTRY_VERSION


def build_goal_hash(goal: dict[str, Any], constraints: dict[str, Any]) -> str:
    """SHA256 of semantic goal + constraints."""
    semantic = {
        "intent": str(goal.get("intent") or "").strip().lower(),
        "objective": str(goal.get("objective") or "").strip(),
        "operator_id": str(goal.get("operator_id") or "").strip(),
        "tenant_id": str(goal.get("tenant_id") or "default").strip(),
        "aais_instance_id": str(goal.get("aais_instance_id") or "").strip(),
        "region_id": str(goal.get("region_id") or "").strip(),
        "constraints": dict(constraints or {}),
    }
    return sha256(_stable_json(semantic).encode("utf-8")).hexdigest()


def build_organ_receipt_tuples(
    gcm: dict[str, Any],
    *,
    registry_version: str | None = None,
    region_id: str = "",
    rail: str = "NORMAL",
    ledger_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Normalize participating organs to receipt tuples with region/rail proof."""
    version = str(registry_version or _default_organs_registry_version())
    region = str(region_id or (gcm.get("goal") or {}).get("region_id") or "").strip()
    rail_upper = str(rail or "NORMAL").upper()
    ledger_by_organ: dict[str, dict[str, Any]] = {}
    for row in list(ledger_rows or []):
        oid = str(row.get("organ_id") or "")
        if oid:
            ledger_by_organ[oid] = row

    tuples: list[dict[str, str]] = []
    for organ in list(gcm.get("participating_organs") or []):
        contract = dict(organ.get("contract") or {})
        ceiling = str(contract.get("risk_ceiling") or "high")
        organ_id = str(organ.get("organ_id") or "")
        row = ledger_by_organ.get(organ_id) or {}
        tuples.append(
            {
                "organ_id": organ_id,
                "provider": str(organ.get("provider") or contract.get("provider") or "local"),
                "contract_version": version,
                "ceiling": ceiling,
                "region_id": str(row.get("region_id") or region),
                "rail": str(row.get("rail") or rail_upper),
            }
        )
    tuples.sort(key=lambda item: item["organ_id"])
    return tuples


def build_invariant_digest(invariant_set: dict[str, Any]) -> str:
    """SHA256 of active cloud invariant families + verdicts."""
    payload = {
        "families": list(invariant_set.get("families") or []),
        "mission_open": list(invariant_set.get("mission_open") or []),
        "per_step": list(invariant_set.get("per_step") or []),
        "all_passed": bool(invariant_set.get("all_passed")),
    }
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def map_outcome(status: str, *, ingress: dict[str, Any] | None = None) -> str:
    """Map runtime status to MissionReceipt outcome enum."""
    normalized = str(status or "").strip().lower()
    if normalized == "ok":
        return OUTCOME_COMPLETED
    if normalized == "rejected":
        return OUTCOME_VETOED
    if ingress and ingress.get("status") != "stamped":
        return OUTCOME_VETOED
    return OUTCOME_FAILED


def _collect_invariant_results(
    *,
    gcm: dict[str, Any] | None,
    block_context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    ctx = dict(block_context or {})
    results.extend(list(ctx.get("invariant_results") or []))
    if gcm:
        inv_set = dict(gcm.get("invariant_set") or {})
        results.extend(list(inv_set.get("mission_open") or []))
        for step in list(inv_set.get("per_step") or []):
            results.extend(list(step.get("results") or []))
    return results


def _has_constraint_invariant_fail(results: list[dict[str, Any]]) -> bool:
    for item in results:
        if str(item.get("status") or "") != "hard_fail":
            continue
        family = str(item.get("family") or "")
        details = str(item.get("details") or "").lower()
        if family in CONSTRAINT_INVARIANT_FAMILIES:
            return True
        if any(
            token in details
            for token in (
                "constraint",
                "region",
                "cost",
                "risk",
                "domain",
                "rail",
                "admitted",
                "denies",
                "b_cloud",
            )
        ):
            return True
    return False


def map_failure_reason(
    *,
    status: str,
    ingress: dict[str, Any] | None = None,
    gcm: dict[str, Any] | None = None,
    block_context: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
) -> str | None:
    """Map runtime failure to diagnostic failure_reason (None when completed)."""
    if map_outcome(status, ingress=ingress) == OUTCOME_COMPLETED:
        return None

    req = dict(request or {})
    ing = dict(ingress or {})
    ctx = dict(block_context or {})

    if req.get("operator_veto") or ing.get("reject_reason") == "operator_veto":
        return FAILURE_REASON_OPERATOR_VETO

    normalized = str(status or "").strip().lower()
    if normalized == "rejected" or ing.get("status") != "stamped":
        return FAILURE_REASON_GATE_REJECTION

    summary = str(ctx.get("summary") or "").lower()
    match_reason = str(ctx.get("match_reason") or "")
    if not match_reason:
        for meta in list(ctx.get("auto_assign_meta") or []):
            mr = str(meta.get("match_reason") or "")
            if mr.startswith("no_admissible_organ") or mr.startswith("explicit_organ_outside"):
                match_reason = mr
                break

    if (
        match_reason.startswith("no_admissible_organ")
        or match_reason.startswith("explicit_organ_outside")
        or "organ not resolved" in summary
    ):
        return FAILURE_REASON_NO_ADMISSIBLE_ORGAN

    if "budget" in summary or "budget_exceeded" in summary:
        return FAILURE_REASON_BUDGET_EXCEEDED

    if _has_constraint_invariant_fail(_collect_invariant_results(gcm=gcm, block_context=block_context)):
        return FAILURE_REASON_UNFULFILLABLE_CONSTRAINTS

    if any(
        token in summary
        for token in ("aais bridge", "duplicate step", "cloud invariants failed", "invariant", "identity")
    ):
        if "organ not resolved" not in summary:
            if "cloud invariants" in summary or "invariant" in summary:
                return FAILURE_REASON_UNFULFILLABLE_CONSTRAINTS
            return FAILURE_REASON_RUNTIME_ERROR

    if normalized == "blocked":
        return FAILURE_REASON_RUNTIME_ERROR

    return FAILURE_REASON_GATE_REJECTION


def build_mission_receipt_v2(
    *,
    gcm: dict[str, Any],
    ingress: dict[str, Any],
    ledger_rows: list[dict[str, Any]],
    registry_version: str | None = None,
    block_context: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
    urg_version: str | None = None,
    rail: str = "NORMAL",
    execution_mode: str | None = None,
    shadow: bool | None = None,
) -> dict[str, Any]:
    """Assemble unsigned MissionReceipt v1.2 (signatures added by receipt_signing)."""
    from src.ugr.invariants.cloud_invariants import check_cloud_identity, has_hard_fail
    from src.ugr.mission.mission_runtime import URG_MISSION_RUNTIME_VERSION

    goal = dict(gcm.get("goal") or {})
    constraints = dict(gcm.get("constraints") or {})
    invariant_set = dict(gcm.get("invariant_set") or {})
    status = str(gcm.get("status") or "")
    outcome = map_outcome(status, ingress=ingress)
    failure_reason = map_failure_reason(
        status=status,
        ingress=ingress,
        gcm=gcm,
        block_context=block_context,
        request=request,
    )

    cloud_identity_hash = str(ingress.get("cloud_identity_hash") or "")
    boundary_digest = str(ingress.get("boundary_digest") or "")
    if status == "ok" and cloud_identity_hash:
        frozen_organs = list(ingress.get("organ_ids") or [])
        identity_results = check_cloud_identity(
            {
                "request": request or {},
                "ingress": ingress,
                "cloud_manifold": {
                    "cloud_identity_hash": cloud_identity_hash,
                    "boundary_digest": boundary_digest,
                    "organ_ids": frozen_organs,
                },
                "organ_ids": frozen_organs,
            },
            authorized_rebind=bool((request or {}).get("authorized_identity_mutation")),
        )
        if has_hard_fail(identity_results):
            raise ValueError(identity_results[0].get("details", "cloud_identity_check_failed"))

    receipt: dict[str, Any] = {
        "schema_version": MISSION_RECEIPT_SCHEMA_VERSION,
        "urg_version": str(urg_version or URG_MISSION_RUNTIME_VERSION),
        "invariant_version": str(ingress.get("invariant_version") or CLOUD_INVARIANT_SET_VERSION),
        "cloud_identity_hash": cloud_identity_hash,
        "boundary_digest": boundary_digest,
        "mission_id": str(gcm.get("mission_id") or ingress.get("mission_id") or ""),
        "mission_slug": ingress.get("mission_slug"),
        "goal_hash": build_goal_hash(goal, constraints),
        "organs": build_organ_receipt_tuples(
            gcm,
            registry_version=registry_version,
            region_id=str(goal.get("region_id") or ""),
            rail=rail,
            ledger_rows=ledger_rows,
        ),
        "invariant_digest": build_invariant_digest(invariant_set),
        "ledger_root": compute_ledger_merkle_root(list(ledger_rows or [])),
        "operator_sig": {
            "operator_id": str(goal.get("operator_id") or ingress.get("operator_id") or ""),
            "tenant_id": str(goal.get("tenant_id") or ingress.get("tenant_id") or "default"),
            "aais_instance_id": str(goal.get("aais_instance_id") or ingress.get("aais_instance_id") or ""),
            "stamped_at": int(ingress.get("stamped_at") or time.time()),
            "operator_mac": None,
            "operator_key_id": None,
        },
        "outcome": outcome,
        "urg_key_id": None,
        "receipt_sig": None,
        "receipt_algorithm": None,
        "issued_at": int(time.time()),
        "gcm_version": gcm.get("gcm_version"),
        "ingress_stamp_hash": ingress.get("stamp_hash"),
    }
    if failure_reason:
        receipt["failure_reason"] = failure_reason
    if execution_mode:
        receipt["execution_mode"] = str(execution_mode).upper()
    if shadow is not None:
        receipt["shadow"] = bool(shadow)
    tenant_digest = str(ingress.get("tenant_manifold_digest") or "")
    if tenant_digest:
        receipt["tenant_manifold_digest"] = tenant_digest
    tenant_norm = str(ingress.get("tenant_normalized_id") or ingress.get("tenant_id") or "")
    if tenant_norm:
        receipt["tenant_normalized_id"] = tenant_norm
    budget_digest = str(ingress.get("budget_digest") or "")
    if budget_digest:
        receipt["budget_digest"] = budget_digest
    if ingress.get("soft_ceil_breached") is not None:
        receipt["soft_ceil_breached"] = bool(ingress.get("soft_ceil_breached"))
    federation_digest = str(ingress.get("federation_digest") or "")
    if federation_digest:
        receipt["federation_digest"] = federation_digest
    counterparty_ref = ingress.get("counterparty_receipt_ref")
    if counterparty_ref:
        receipt["counterparty_receipt_ref"] = dict(counterparty_ref)
    return receipt


def build_federation_receipt_fields(
    *,
    runtime_dir: Union[str, Path],
    home_tenant_id: str,
    mission_id: str,
    federation_context: list[dict[str, Any]],
) -> tuple[str | None, dict[str, Any] | None]:
    """Compute federation_digest and counterparty_receipt_ref for v1.8 receipts."""
    from src.ugr.mission.federation_grants import compute_federation_digest
    from src.ugr.mission.mission_ledger import MissionLedger
    from src.ugr.platform.tenant_registry import normalize_tenant_id

    if not federation_context:
        return None, None
    grant_id = str(federation_context[0].get("grant_id") or "")
    peer_tenant = normalize_tenant_id(
        str(federation_context[0].get("peer_tenant") or "")
    )
    root = Path(runtime_dir)
    home_ledger = MissionLedger(runtime_dir=root, tenant_id=home_tenant_id)
    peer_ledger = MissionLedger(runtime_dir=root, tenant_id=peer_tenant)
    home_rows = home_ledger.list_for_mission(mission_id)
    peer_rows = peer_ledger.list_for_mission(mission_id)
    digest = compute_federation_digest(
        home_rows=home_rows,
        peer_rows=peer_rows,
        grant_id=grant_id,
    )
    peer_rows_fed = [
        r
        for r in peer_rows
        if r.get("phase") in {"federation_inbound", "federation_governance_inbound"}
    ]
    receipt_row_hash = ""
    if peer_rows_fed:
        receipt_row_hash = sha256(
            _stable_json(peer_rows_fed[-1]).encode("utf-8")
        ).hexdigest()
    counterparty_ref = {
        "tenant_id": peer_tenant,
        "mission_id": mission_id,
        "receipt_row_hash": receipt_row_hash,
        "grant_id": grant_id,
    }
    return digest, counterparty_ref
