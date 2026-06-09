"""Governance IR — single clock-tick law snapshot for the invariant compiler."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from src.cisiv import normalize_cisiv_stage
from src.ugr.discovery.standing import Standing, label_from_standing, standing_from_label


GOVERNANCE_IR_VERSION = "aais.governance_ir.v1"
DEFAULT_MAX_SUBAGENT_DEPTH = 3

BASE_HARD_INVARIANTS = (
    "packet_shape_complete",
    "payload_present",
    "runtime_context_explicit",
    "governance_packet_emitted",
    "structured_trace_emitted",
    "aris_runtime_boundary_enforced",
    "aris_does_not_self_apply",
)

CONDITIONAL_INVARIANT_PREDICATES = {
    "effectful_execution_is_governed": "effectful",
    "verification_alignment_required": "effectful",
    "approval_state_declared": "requires_approval",
    "model_only_sources_cannot_self_execute": "model_only_source",
    "non_copy_clause_enforced": "external_suggestion",
    "shared_patterns_are_signature_only": "share_mode_present",
}

STAGE_LINKED_INVARIANTS = {
    "concept": ("ingress_protocol_checked",),
    "identity": ("governance_packet_emitted",),
    "structure": ("structured_trace_emitted",),
    "implementation": ("governed_llm_proposal_required",),
    "verification": ("verification_alignment_required",),
}

SAFE_VERBS = frozenset({"observe", "respond", "route"})
PROPOSE_VERBS = frozenset({"propose", "deliberate"})
EXECUTE_VERBS = frozenset({"execute", "mutate", "apply"})


class GovernanceIRValidationError(ValueError):
    """Raised when bridge inputs cannot produce a valid Governance IR."""


@dataclass(frozen=True)
class AuthorityEnvelope:
    principal: dict[str, Any]
    resources: tuple[str, ...]
    allowed_verbs: tuple[str, ...]
    capabilities: tuple[str, ...]
    delegation_depth: int
    max_subagent_depth: int


@dataclass(frozen=True)
class ConditionalInvariant:
    name: str
    predicate: str


@dataclass(frozen=True)
class InvariantSet:
    hard: tuple[str, ...]
    conditional: tuple[ConditionalInvariant, ...]
    stage_linked: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class ExecutionContext:
    cisiv_stage: str
    otem_level: str
    otem_boundary: dict[str, Any]
    subagent_lineage: tuple[dict[str, Any], ...]
    odl_anchor: dict[str, Any]


@dataclass(frozen=True)
class GovernanceIR:
    ir_version: str
    clock_tick_id: str
    compiled_at: str
    ir_fingerprint: str
    authority_envelope: AuthorityEnvelope
    invariant_set: InvariantSet
    execution_context: ExecutionContext


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _classify_invariants(
    derived: tuple[str, ...],
    *,
    effectful: bool,
    requires_approval: bool,
    model_only_source: bool,
    external_suggestion: bool,
    share_mode_present: bool,
) -> InvariantSet:
    derived_set = set(derived)
    hard = tuple(name for name in BASE_HARD_INVARIANTS if name in derived_set)
    conditional: list[ConditionalInvariant] = []
    for name, predicate in CONDITIONAL_INVARIANT_PREDICATES.items():
        if name not in derived_set:
            continue
        active = {
            "effectful": effectful,
            "requires_approval": requires_approval,
            "model_only_source": model_only_source,
            "external_suggestion": external_suggestion,
            "share_mode_present": share_mode_present,
        }.get(predicate, True)
        if active:
            conditional.append(ConditionalInvariant(name=name, predicate=predicate))
    stage_linked = {
        stage: tuple(inv for inv in invariants if inv in derived_set)
        for stage, invariants in STAGE_LINKED_INVARIANTS.items()
    }
    return InvariantSet(hard=hard, conditional=tuple(conditional), stage_linked=stage_linked)


def _derive_allowed_verbs(
    execution_intent: str,
    *,
    effectful: bool,
    packet_type: str,
) -> tuple[str, ...]:
    intent = str(execution_intent or "observe").strip().lower()
    verbs: list[str] = []
    if intent in SAFE_VERBS:
        verbs.append(intent)
    elif intent in PROPOSE_VERBS:
        verbs.extend(["observe", intent])
    elif intent in EXECUTE_VERBS:
        verbs.extend(["observe", "propose", intent])
    else:
        verbs.append("observe")
    if packet_type in {"deliberation_request", "generation_request"}:
        if "propose" not in verbs:
            verbs.append("propose")
    if effectful and "execute" not in verbs:
        verbs.append("execute")
    return tuple(dict.fromkeys(verbs))


def _derive_capabilities(
    *,
    effectful: bool,
    packet_type: str,
    proposal_only: bool = True,
) -> tuple[str, ...]:
    caps: list[str] = ["governed_ingress"]
    if packet_type in {"deliberation_request", "generation_request"}:
        caps.append("governed_llm")
    if proposal_only:
        caps.append("proposal_only")
    if effectful:
        caps.append("effectful_execution")
    return tuple(caps)


def _derive_resources(normalized: dict[str, Any], governance: dict[str, Any]) -> tuple[str, ...]:
    payload = dict(normalized.get("payload") or {})
    resources: list[str] = []
    for key in ("session_id", "trace_id", "mission_id", "workspace_id", "scope_id"):
        value = str(payload.get(key) or "").strip()
        if value:
            resources.append(f"{key}:{value}")
    runtime_context = str(governance.get("runtime_context") or "live_runtime")
    resources.append(f"runtime_context:{runtime_context}")
    packet_type = str(governance.get("packet_type") or normalized.get("type") or "unknown")
    resources.append(f"packet_type:{packet_type}")
    return tuple(dict.fromkeys(resources))


def _build_principal(
    normalized: dict[str, Any],
    authority_snapshot: dict[str, Any] | None,
    standing: str | int | None,
) -> dict[str, Any]:
    payload = dict(normalized.get("payload") or {})
    snapshot = dict(authority_snapshot or {})
    standing_value = standing
    if standing_value is None:
        standing_value = snapshot.get("standing") or snapshot.get("standing_label")
    if isinstance(standing_value, (int, Standing)):
        standing_label = label_from_standing(standing_value)
    else:
        standing_label = label_from_standing(standing_from_label(str(standing_value or "asserted")))
    return {
        "actor_id": str(payload.get("actor_id") or payload.get("source_id") or normalized.get("source") or "unknown"),
        "session_id": payload.get("session_id"),
        "tenant_id": payload.get("tenant_id"),
        "standing_label": standing_label,
        "primary_authority_source": snapshot.get("primary_source"),
    }


def _build_subagent_lineage(
    normalized: dict[str, Any],
    runtime_context: dict[str, Any] | None,
) -> tuple[dict[str, Any], ...]:
    payload = dict(normalized.get("payload") or {})
    ctx = dict(runtime_context or payload.get("runtime_context_payload") or {})
    lineage: list[dict[str, Any]] = []
    if payload.get("bridge_id") or payload.get("parent_bridge_id"):
        lineage.append(
            {
                "bridge_id": payload.get("bridge_id") or payload.get("parent_bridge_id"),
                "mission_id": payload.get("mission_id"),
            }
        )
    for item in list(ctx.get("subagent_lineage") or []):
        if isinstance(item, dict):
            lineage.append(dict(item))
    depth = len(lineage)
    return tuple(lineage), depth


def _normalize_odl_anchor(odl_anchor: dict[str, Any] | None) -> dict[str, Any]:
    anchor = dict(odl_anchor or {})
    return {
        "decision_id": anchor.get("decision_id"),
        "causal_parents": list(anchor.get("causal_parents") or []),
        "scope_id": anchor.get("scope_id"),
    }


def _normalize_otem(otem_boundary: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    boundary = dict(otem_boundary or {})
    level = str(boundary.get("level") or boundary.get("otem_level") or "none").strip().lower()
    if level not in {"none", "detected", "approved", "blocked"}:
        level = "detected" if boundary.get("detected") else "none"
    return level, boundary


def governance_ir_to_dict(ir: GovernanceIR) -> dict[str, Any]:
    payload = asdict(ir)
    payload["invariant_set"]["conditional"] = [
        {"name": item.name, "predicate": item.predicate} for item in ir.invariant_set.conditional
    ]
    payload["invariant_set"]["stage_linked"] = {
        stage: list(invariants) for stage, invariants in ir.invariant_set.stage_linked.items()
    }
    payload["authority_envelope"]["resources"] = list(ir.authority_envelope.resources)
    payload["authority_envelope"]["allowed_verbs"] = list(ir.authority_envelope.allowed_verbs)
    payload["authority_envelope"]["capabilities"] = list(ir.authority_envelope.capabilities)
    payload["execution_context"]["subagent_lineage"] = list(ir.execution_context.subagent_lineage)
    return payload


def build_governance_ir(
    *,
    bridge_result: dict[str, Any] | None = None,
    authority_snapshot: dict[str, Any] | None = None,
    standing: str | int | None = None,
    runtime_context: dict[str, Any] | None = None,
    odl_anchor: dict[str, Any] | None = None,
    otem_boundary: dict[str, Any] | None = None,
    cisiv_stage: str | None = None,
) -> dict[str, Any]:
    """Build one Governance IR dict from bridge clearance and authority context."""
    bridge = dict(bridge_result or {})
    normalized = dict(bridge.get("normalized_input") or {})
    governance = dict(bridge.get("governance_packet") or {})
    if not normalized or not governance:
        raise GovernanceIRValidationError("bridge_result must include normalized_input and governance_packet")

    source = str(normalized.get("source") or governance.get("source") or "").strip().lower()
    packet_type = str(normalized.get("type") or governance.get("packet_type") or "").strip().lower()
    payload = dict(normalized.get("payload") or {})
    effectful = bool(governance.get("effectful") or normalized.get("effectful"))
    requires_approval = bool(governance.get("requires_approval") or normalized.get("requires_approval"))
    execution_intent = str(
        governance.get("execution_intent") or normalized.get("execution_intent") or payload.get("execution_intent") or "observe"
    ).strip().lower()
    derived = tuple(governance.get("invariants") or ())
    if not derived:
        from src.cognitive_bridge import _derive_invariants

        derived = _derive_invariants(
            source=source,
            packet_type=packet_type,
            payload=payload,
            effectful=effectful,
            requires_approval=requires_approval,
        )

    share_mode_present = any(
        key in payload
        for key in (
            "pattern_share_mode",
            "collective_share_mode",
            "export_mode",
            "share_mode",
            "content_transfer_mode",
        )
    )
    invariant_set = _classify_invariants(
        derived,
        effectful=effectful,
        requires_approval=requires_approval,
        model_only_source=source in {"llm", "predictor", "swarm"},
        external_suggestion=bool(payload.get("external_suggestion") or payload.get("external_suggestion_present")),
        share_mode_present=share_mode_present,
    )

    lineage, delegation_depth = _build_subagent_lineage(normalized, runtime_context)
    otem_level, otem_boundary_norm = _normalize_otem(
        otem_boundary or payload.get("otem_boundary") or bridge.get("otem_boundary")
    )
    stage = normalize_cisiv_stage(
        cisiv_stage or payload.get("cisiv_stage") or bridge.get("cisiv_stage"),
        default="implementation",
    )

    authority = AuthorityEnvelope(
        principal=_build_principal(normalized, authority_snapshot, standing),
        resources=_derive_resources(normalized, governance),
        allowed_verbs=_derive_allowed_verbs(execution_intent, effectful=effectful, packet_type=packet_type),
        capabilities=_derive_capabilities(effectful=effectful, packet_type=packet_type),
        delegation_depth=delegation_depth,
        max_subagent_depth=int(payload.get("max_subagent_depth") or DEFAULT_MAX_SUBAGENT_DEPTH),
    )
    execution = ExecutionContext(
        cisiv_stage=stage,
        otem_level=otem_level,
        otem_boundary=otem_boundary_norm,
        subagent_lineage=lineage,
        odl_anchor=_normalize_odl_anchor(odl_anchor or payload.get("odl_anchor")),
    )
    clock_tick_id = str(
        governance.get("packet_fingerprint")
        or bridge.get("bridge_id")
        or _fingerprint({"normalized": normalized, "governance": governance})
    )
    numeric_otem_level = None
    authority_band_label = None
    containment_mode = False
    otem_ceiling_rules: dict[str, Any] = {}
    law_registry: dict[str, Any] = {}
    try:
        from src.otem_capability import authority_band, get_otem_capability_level
        from src.otem_ceiling import default_law_registry, otem_ceiling

        numeric_otem_level = get_otem_capability_level()
        otem_ceiling_rules = otem_ceiling.rules_for_ir()
        law_registry = default_law_registry()
        authority_band_label = str(otem_ceiling_rules.get("authority_band") or authority_band(numeric_otem_level))
        containment_mode = bool(otem_ceiling_rules.get("containment_mode"))
        numeric_otem_level = int(otem_ceiling_rules.get("numeric_level") or numeric_otem_level)
        odl_root = str(otem_ceiling_rules.get("odl_root_id") or "").strip()
        if odl_root and not execution.odl_anchor.get("decision_id"):
            execution = ExecutionContext(
                cisiv_stage=execution.cisiv_stage,
                otem_level=execution.otem_level,
                otem_boundary=execution.otem_boundary,
                subagent_lineage=execution.subagent_lineage,
                odl_anchor={
                    "decision_id": odl_root,
                    "causal_parents": list(execution.odl_anchor.get("causal_parents") or []),
                    "scope_id": execution.odl_anchor.get("scope_id"),
                },
            )
    except Exception:
        try:
            from src.otem_capability import authority_band, get_otem_capability_level
            from src.otem_ceiling import default_law_registry, default_rules_snapshot

            numeric_otem_level = get_otem_capability_level()
            authority_band_label = authority_band(numeric_otem_level)
            otem_ceiling_rules = default_rules_snapshot(numeric_level=numeric_otem_level)
            law_registry = default_law_registry()
        except Exception:
            pass

    ir_body = {
        "ir_version": GOVERNANCE_IR_VERSION,
        "clock_tick_id": clock_tick_id,
        "compiled_at": _utc_now(),
        "authority_envelope": asdict(authority),
        "invariant_set": {
            "hard": list(invariant_set.hard),
            "conditional": [{"name": c.name, "predicate": c.predicate} for c in invariant_set.conditional],
            "stage_linked": {k: list(v) for k, v in invariant_set.stage_linked.items()},
        },
        "execution_context": {
            "cisiv_stage": execution.cisiv_stage,
            "otem_level": execution.otem_level,
            "otem_boundary": execution.otem_boundary,
            "subagent_lineage": list(execution.subagent_lineage),
            "odl_anchor": execution.odl_anchor,
            "numeric_otem_level": numeric_otem_level,
            "authority_band": authority_band_label,
            "containment_mode": containment_mode,
        },
        "otem_ceiling_rules": otem_ceiling_rules,
        "law_registry": law_registry,
    }
    ir_fingerprint = _fingerprint(ir_body)
    ir_body["ir_fingerprint"] = ir_fingerprint
    return ir_body
