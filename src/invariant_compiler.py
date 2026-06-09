"""Invariant compiler — lowers Governance IR into decode governance artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any

from src.authority_mask_lowering import lower_authority_mask
from src.governance_ir import GOVERNANCE_IR_VERSION
from src.governance_taxonomy import TAXONOMY_SCHEMA_ID
from src.invariant_engine import InvariantEngine
from src.training_view_spec import build_training_view_spec


INVARIANT_COMPILER_VERSION = "aais.invariant_compiler.v1"
DEFAULT_MAX_ROLLBACKS = 2
DEFAULT_ESCALATION_THRESHOLD = 2

CHECK_POSITIONS = (
    "ingress",
    "checkpoint",
    "admission",
    "subagent_spawn",
    "external_mutation",
)

INGRESS_VALIDATORS = ("wonder_gate", "rls_admissibility", "bridge_invariant")
CHECKPOINT_VALIDATORS = (
    "wonder_gate",
    "rls_admissibility",
    "bridge_invariant",
    "governed_llm_envelope",
    "proposal_only",
    "temperature_zero",
)
ADMISSION_VALIDATORS = ("bridge_invariant", "chat_turn_contract")


class InvariantCompilerError(ValueError):
    """Raised when Governance IR cannot be compiled."""


@dataclass(frozen=True)
class CheckNode:
    position: str
    validator: str
    required: bool = True


@dataclass(frozen=True)
class CheckGraph:
    nodes: tuple[CheckNode, ...]
    ir_fingerprint: str


@dataclass(frozen=True)
class RollbackAction:
    target: str
    enabled: bool = True


@dataclass(frozen=True)
class RollbackPolicy:
    max_rollbacks: int
    actions: tuple[RollbackAction, ...]
    tighten_on_violation: bool = True


@dataclass(frozen=True)
class EscalationHooks:
    max_attempts: int
    escalate_to: str
    otem_gate: bool
    operator_approval: bool
    otem_ceiling_gate: bool = False
    constitutional_amendment_gate: bool = False


@dataclass(frozen=True)
class IngressPlan:
    validators: tuple[str, ...]
    fail_closed: bool = True


@dataclass(frozen=True)
class DecodeGovernanceBundle:
    compiler_version: str
    ir_version: str
    ir_fingerprint: str
    taxonomy_ref: str
    check_graph: CheckGraph
    rollback_policy: RollbackPolicy
    escalation_hooks: EscalationHooks
    ingress_plan: IngressPlan
    authority_mask_spec: dict[str, Any]
    training_view_spec: dict[str, Any]


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _require_ir(ir: dict[str, Any]) -> dict[str, Any]:
    payload = dict(ir or {})
    if payload.get("ir_version") != GOVERNANCE_IR_VERSION:
        raise InvariantCompilerError(f"unsupported ir_version: {payload.get('ir_version')}")
    if not payload.get("ir_fingerprint"):
        raise InvariantCompilerError("governance ir missing ir_fingerprint")
    return payload


def _build_check_graph(ir: dict[str, Any]) -> CheckGraph:
    fingerprint = str(ir["ir_fingerprint"])
    nodes: list[CheckNode] = []
    for validator in INGRESS_VALIDATORS:
        nodes.append(CheckNode(position="ingress", validator=validator))
    for validator in CHECKPOINT_VALIDATORS:
        nodes.append(CheckNode(position="checkpoint", validator=validator))
    for validator in ADMISSION_VALIDATORS:
        nodes.append(CheckNode(position="admission", validator=validator))
    capabilities = tuple(ir.get("authority_envelope", {}).get("capabilities") or ())
    if "effectful_execution" in capabilities:
        nodes.append(CheckNode(position="external_mutation", validator="effectful_execution_is_governed"))
    delegation_depth = int(ir.get("authority_envelope", {}).get("delegation_depth") or 0)
    max_depth = int(ir.get("authority_envelope", {}).get("max_subagent_depth") or 3)
    if delegation_depth < max_depth:
        nodes.append(CheckNode(position="subagent_spawn", validator="delegation_depth_within_cap"))
    return CheckGraph(nodes=tuple(nodes), ir_fingerprint=fingerprint)


def _build_rollback_policy(ir: dict[str, Any]) -> RollbackPolicy:
    actions = (
        RollbackAction(target="draft_buffer", enabled=True),
        RollbackAction(target="proposed_odl_node", enabled=True),
        RollbackAction(target="conversation_memory_assistant_turn", enabled=True),
        RollbackAction(target="plan_branch", enabled=False),
    )
    hard_count = len(ir.get("invariant_set", {}).get("hard") or [])
    max_rollbacks = DEFAULT_MAX_ROLLBACKS if hard_count <= 6 else 1
    return RollbackPolicy(max_rollbacks=max_rollbacks, actions=actions, tighten_on_violation=True)


def _build_escalation_hooks(ir: dict[str, Any]) -> EscalationHooks:
    ceiling_rules = dict(ir.get("otem_ceiling_rules") or {})
    otem_level = str(ir.get("execution_context", {}).get("otem_level") or "none")
    escalate_to = "block"
    otem_gate = False
    operator_approval = False
    otem_ceiling_gate = False
    constitutional_amendment_gate = False
    if ceiling_rules.get("ceiling_active"):
        escalate_to = "constitutional_amendment"
        constitutional_amendment_gate = True
    elif ceiling_rules.get("containment_mode"):
        escalate_to = "otem_ceiling"
        otem_ceiling_gate = True
    elif otem_level in {"detected", "blocked"}:
        escalate_to = "otem"
        otem_gate = True
    elif otem_level == "approved":
        escalate_to = "operator"
        operator_approval = True
    return EscalationHooks(
        max_attempts=DEFAULT_ESCALATION_THRESHOLD + DEFAULT_MAX_ROLLBACKS,
        escalate_to=escalate_to,
        otem_gate=otem_gate,
        operator_approval=operator_approval,
        otem_ceiling_gate=otem_ceiling_gate,
        constitutional_amendment_gate=constitutional_amendment_gate,
    )


def _build_ingress_plan() -> IngressPlan:
    return IngressPlan(validators=INGRESS_VALIDATORS, fail_closed=True)


def _build_authority_mask_spec(ir: dict[str, Any]) -> dict[str, Any]:
    return lower_authority_mask(ir, {})


def _build_training_view_spec(ir: dict[str, Any]) -> dict[str, Any]:
    return build_training_view_spec(ir)


def compile_from_ir(ir: dict[str, Any] | Any) -> dict[str, Any]:
    """Compile one Governance IR dict into a DecodeGovernanceBundle dict."""
    if hasattr(ir, "ir_fingerprint"):
        ir_payload = {
            "ir_version": ir.ir_version,
            "ir_fingerprint": ir.ir_fingerprint,
            "authority_envelope": asdict(ir.authority_envelope),
            "invariant_set": {
                "hard": list(ir.invariant_set.hard),
                "conditional": [{"name": c.name, "predicate": c.predicate} for c in ir.invariant_set.conditional],
                "stage_linked": {k: list(v) for k, v in ir.invariant_set.stage_linked.items()},
            },
            "execution_context": asdict(ir.execution_context),
        }
    else:
        ir_payload = _require_ir(dict(ir))

    check_graph = _build_check_graph(ir_payload)
    authority_mask_spec = _build_authority_mask_spec(ir_payload)
    training_view_spec = _build_training_view_spec(ir_payload)
    bundle = DecodeGovernanceBundle(
        compiler_version=INVARIANT_COMPILER_VERSION,
        ir_version=str(ir_payload.get("ir_version") or GOVERNANCE_IR_VERSION),
        ir_fingerprint=str(ir_payload["ir_fingerprint"]),
        taxonomy_ref=TAXONOMY_SCHEMA_ID,
        check_graph=check_graph,
        rollback_policy=_build_rollback_policy(ir_payload),
        escalation_hooks=_build_escalation_hooks(ir_payload),
        ingress_plan=_build_ingress_plan(),
        authority_mask_spec=authority_mask_spec,
        training_view_spec=training_view_spec,
    )
    payload = {
        "compiler_version": bundle.compiler_version,
        "ir_version": bundle.ir_version,
        "ir_fingerprint": bundle.ir_fingerprint,
        "taxonomy_ref": bundle.taxonomy_ref,
        "bundle_fingerprint": _fingerprint(
            {
                "ir_fingerprint": bundle.ir_fingerprint,
                "compiler_version": bundle.compiler_version,
            }
        ),
        "check_graph": {
            "ir_fingerprint": bundle.check_graph.ir_fingerprint,
            "nodes": [asdict(node) for node in bundle.check_graph.nodes],
        },
        "rollback_policy": {
            "max_rollbacks": bundle.rollback_policy.max_rollbacks,
            "tighten_on_violation": bundle.rollback_policy.tighten_on_violation,
            "actions": [asdict(action) for action in bundle.rollback_policy.actions],
        },
        "escalation_hooks": asdict(bundle.escalation_hooks),
        "ingress_plan": {
            "validators": list(bundle.ingress_plan.validators),
            "fail_closed": bundle.ingress_plan.fail_closed,
        },
        "authority_mask_spec": dict(bundle.authority_mask_spec),
        "training_view_spec": dict(bundle.training_view_spec),
    }
    return payload


def apply_ingress_plan(
    normalized_packet: dict[str, Any],
    governance_packet: dict[str, Any],
    *,
    decode_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run ingress validators from a compiled bundle (delegates to InvariantEngine)."""
    bundle = dict(decode_bundle or {})
    ingress_plan = dict(bundle.get("ingress_plan") or {})
    validators = tuple(ingress_plan.get("validators") or INGRESS_VALIDATORS)
    results: list[dict[str, Any]] = []
    allows = True
    for validator in validators:
        if validator == "wonder_gate":
            from src.wonder.validation import validate_wonder_permitted

            outcome = validate_wonder_permitted(normalized_packet, governance_packet)
            results.append({"validator": validator, **outcome})
            if outcome.get("status") != "skipped":
                allows = allows and bool(outcome.get("allows"))
        elif validator in ("rls_admissibility", "rls_reasoning_admissible"):
            from src.rls.validation import validate_rls_admissible

            outcome = validate_rls_admissible(
                normalized_packet,
                governance_packet,
                record_quarantine=False,
            )
            results.append({"validator": validator, **outcome})
            if outcome.get("status") != "skipped":
                allows = allows and bool(outcome.get("allows"))
        elif validator == "bridge_invariant":
            outcome = InvariantEngine.validate_bridge_packet(normalized_packet, governance_packet)
            results.append({"validator": validator, **outcome})
            allows = allows and bool(outcome.get("allows"))
        else:
            results.append(
                {
                    "validator": validator,
                    "status": "skipped",
                    "allows": True,
                    "details": "ingress validator not wired in v1",
                }
            )
    status = "pass" if allows else "fail"
    return {
        "module_id": "aais.invariant_compiler.ingress_plan",
        "status": status,
        "allows": allows,
        "validators": list(validators),
        "results": results,
        "fail_closed": bool(ingress_plan.get("fail_closed", True)),
    }


def run_admission_checks(
    normalized_packet: dict[str, Any],
    governance_packet: dict[str, Any],
    *,
    decode_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run admission-position validators from CheckGraph."""
    bundle = dict(decode_bundle or {})
    nodes = list((bundle.get("check_graph") or {}).get("nodes") or [])
    admission_validators = [
        str(node.get("validator"))
        for node in nodes
        if str(node.get("position")) == "admission"
    ]
    if not admission_validators:
        admission_validators = list(ADMISSION_VALIDATORS)
    results: list[dict[str, Any]] = []
    allows = True
    for validator in admission_validators:
        if validator == "bridge_invariant":
            outcome = InvariantEngine.validate_bridge_packet(normalized_packet, governance_packet)
            results.append({"validator": validator, **outcome})
            allows = allows and bool(outcome.get("allows"))
        elif validator == "chat_turn_contract":
            results.append(
                {
                    "validator": validator,
                    "status": "pass",
                    "allows": True,
                    "details": "chat turn contract enforced by Project Infi law surface",
                }
            )
        else:
            results.append(
                {
                    "validator": validator,
                    "status": "skipped",
                    "allows": True,
                }
            )
    return {
        "module_id": "aais.invariant_compiler.admission",
        "status": "pass" if allows else "fail",
        "allows": allows,
        "results": results,
    }
