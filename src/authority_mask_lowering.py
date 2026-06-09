"""Authority mask lowering — IR to provider-agnostic MaskSpec."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any

from src.governance_ir import EXECUTE_VERBS, GOVERNANCE_IR_VERSION, PROPOSE_VERBS, SAFE_VERBS
from src.governance_taxonomy import (
    AUTHORITY_VERBS,
    MASKABLE_SITE_IDS,
    TAXONOMY_SCHEMA_ID,
    action_class_for_verb,
    allowed_actions_for_stage,
    effective_max_action_class,
    normalize_resource_classes,
    taxonomy_fingerprint,
)

MASK_SPEC_SCHEMA_ID = "nova.authority_mask_spec.v1"

_ACTION_CLASS_RANK = {"observe": 0, "propose": 1, "execute": 2}

_BASE_DENY_PATTERNS = (
    "unauthorized_execute",
    "raw_secret_leak",
    "unsigned_tool_call",
)

_INVARIANT_DENY_PATTERNS = {
    "model_only_sources_cannot_self_execute": "model_only_self_execute",
    "effectful_execution_is_governed": "ungoverned_effectful_execution",
}


@dataclass(frozen=True)
class MaskableSite:
    site_id: str
    position_hint: str
    constraint_schema_ref: str


@dataclass(frozen=True)
class MaskConstraint:
    allowed_verbs: tuple[str, ...]
    forbidden_verbs: tuple[str, ...]
    allowed_resource_classes: tuple[str, ...]
    max_action_class: str
    allowed_action_classes: tuple[str, ...]
    max_child_scope: int | None = None
    deny_patterns: tuple[str, ...] = ()
    denied: bool = False


@dataclass(frozen=True)
class MaskSpec:
    mask_id: str
    schema_id: str
    status: str
    ir_fingerprint: str
    taxonomy_fingerprint: str
    sites: dict[str, MaskConstraint]
    maskable_sites: tuple[MaskableSite, ...]
    provider_hints: dict[str, Any]


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _ir_payload(ir: dict[str, Any] | Any) -> dict[str, Any]:
    if hasattr(ir, "ir_fingerprint"):
        return {
            "ir_version": ir.ir_version,
            "ir_fingerprint": ir.ir_fingerprint,
            "authority_envelope": asdict(ir.authority_envelope),
            "invariant_set": {
                "hard": list(ir.invariant_set.hard),
                "conditional": [
                    {"name": c.name, "predicate": c.predicate} for c in ir.invariant_set.conditional
                ],
                "stage_linked": {k: list(v) for k, v in ir.invariant_set.stage_linked.items()},
            },
            "execution_context": asdict(ir.execution_context),
        }
    return dict(ir or {})


def _verbs_for_max_action_class(max_class: str) -> frozenset[str]:
    rank = _ACTION_CLASS_RANK.get(max_class, 2)
    allowed: set[str] = set()
    if rank >= _ACTION_CLASS_RANK["observe"]:
        allowed |= set(SAFE_VERBS)
    if rank >= _ACTION_CLASS_RANK["propose"]:
        allowed |= set(PROPOSE_VERBS)
    if rank >= _ACTION_CLASS_RANK["execute"]:
        allowed |= set(EXECUTE_VERBS)
    return frozenset(allowed)


def _intersect_verbs(envelope_verbs: tuple[str, ...], cap_class: str) -> tuple[str, ...]:
    cap_verbs = _verbs_for_max_action_class(cap_class)
    normalized = tuple(
        sorted(
            {
                str(verb).strip().lower()
                for verb in envelope_verbs
                if str(verb).strip().lower() in cap_verbs
            }
        )
    )
    return normalized or tuple(sorted(cap_verbs & set(envelope_verbs or ()) or SAFE_VERBS))


def _deny_patterns_from_invariants(ir: dict[str, Any]) -> tuple[str, ...]:
    patterns = list(_BASE_DENY_PATTERNS)
    invariant_set = dict(ir.get("invariant_set") or {})
    hard = set(invariant_set.get("hard") or ())
    conditional = {item.get("name") for item in invariant_set.get("conditional") or () if isinstance(item, dict)}
    stage_linked = invariant_set.get("stage_linked") or {}
    stage = str(ir.get("execution_context", {}).get("cisiv_stage") or "implementation")
    stage_names = set(stage_linked.get(stage) or ())
    for invariant_name, pattern in _INVARIANT_DENY_PATTERNS.items():
        if invariant_name in hard or invariant_name in conditional or invariant_name in stage_names:
            patterns.append(pattern)
    return tuple(dict.fromkeys(patterns))


def _maskable_site_catalog() -> tuple[MaskableSite, ...]:
    return (
        MaskableSite(
            site_id="tool_call_schema",
            position_hint="structured_tool_emission",
            constraint_schema_ref="nova.mask_constraint.tool_call_schema.v1",
        ),
        MaskableSite(
            site_id="external_mutation_command",
            position_hint="shell_file_network_provider_mutation",
            constraint_schema_ref="nova.mask_constraint.external_mutation_command.v1",
        ),
        MaskableSite(
            site_id="subagent_spawn_descriptor",
            position_hint="child_agent_spawn_payload",
            constraint_schema_ref="nova.mask_constraint.subagent_spawn_descriptor.v1",
        ),
        MaskableSite(
            site_id="cisiv_stage_transition",
            position_hint="lifecycle_stage_advance",
            constraint_schema_ref="nova.mask_constraint.cisiv_stage_transition.v1",
        ),
    )


def _site_constraint(
    *,
    site_id: str,
    envelope_verbs: tuple[str, ...],
    resource_classes: tuple[str, ...],
    max_action_class: str,
    allowed_action_classes: frozenset[str],
    deny_patterns: tuple[str, ...],
    max_child_scope: int | None = None,
    denied: bool = False,
) -> MaskConstraint:
    if denied:
        return MaskConstraint(
            allowed_verbs=(),
            forbidden_verbs=tuple(sorted(AUTHORITY_VERBS)),
            allowed_resource_classes=(),
            max_action_class="observe",
            allowed_action_classes=("observe",),
            max_child_scope=0,
            deny_patterns=deny_patterns,
            denied=True,
        )
    allowed_verbs = _intersect_verbs(envelope_verbs, max_action_class)
    forbidden_verbs = tuple(sorted(set(AUTHORITY_VERBS) - set(allowed_verbs)))
    if site_id == "external_mutation_command":
        allowed_verbs = tuple(v for v in allowed_verbs if v in EXECUTE_VERBS or v in PROPOSE_VERBS)
        if max_action_class == "observe":
            allowed_verbs = ()
        forbidden_verbs = tuple(sorted(set(AUTHORITY_VERBS) - set(allowed_verbs)))
    if site_id == "cisiv_stage_transition":
        allowed_verbs = tuple(v for v in allowed_verbs if action_class_for_verb(v) in allowed_action_classes)
        forbidden_verbs = tuple(sorted(set(AUTHORITY_VERBS) - set(allowed_verbs)))
    return MaskConstraint(
        allowed_verbs=allowed_verbs,
        forbidden_verbs=forbidden_verbs,
        allowed_resource_classes=resource_classes,
        max_action_class=max_action_class,
        allowed_action_classes=tuple(sorted(allowed_action_classes)),
        max_child_scope=max_child_scope,
        deny_patterns=deny_patterns,
        denied=denied,
    )


def lower_authority_mask(
    ir: dict[str, Any] | Any,
    decode_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure IR → mask lowering."""
    payload = _ir_payload(ir)
    if payload.get("ir_version") != GOVERNANCE_IR_VERSION:
        raise ValueError(f"unsupported ir_version: {payload.get('ir_version')}")
    ir_fingerprint = str(payload.get("ir_fingerprint") or "")
    if not ir_fingerprint:
        raise ValueError("governance ir missing ir_fingerprint")

    envelope = dict(payload.get("authority_envelope") or {})
    execution_context = dict(payload.get("execution_context") or {})
    envelope_verbs = tuple(str(v).strip().lower() for v in envelope.get("allowed_verbs") or ())
    resource_classes = normalize_resource_classes(envelope.get("resources"))
    delegation_depth = int(envelope.get("delegation_depth") or 0)
    max_subagent_depth = int(envelope.get("max_subagent_depth") or 0)
    otem_level = str(execution_context.get("otem_level") or "none")
    cisiv_stage = str(execution_context.get("cisiv_stage") or "implementation")
    ceiling_rules = dict(payload.get("otem_ceiling_rules") or execution_context.get("otem_ceiling_rules") or {})
    max_action_class = effective_max_action_class(
        otem_level=otem_level,
        authority_band=str(ceiling_rules.get("authority_band") or execution_context.get("authority_band") or ""),
        ceiling_active=bool(ceiling_rules.get("ceiling_active") or execution_context.get("ceiling_active")),
        containment_mode=bool(ceiling_rules.get("containment_mode") or execution_context.get("containment_mode")),
    )
    allowed_action_classes = allowed_actions_for_stage(cisiv_stage)
    deny_patterns = _deny_patterns_from_invariants(payload)
    spawn_denied = max_subagent_depth <= 0 or delegation_depth >= max_subagent_depth
    remaining_child_scope = max(0, max_subagent_depth - delegation_depth)

    sites: dict[str, MaskConstraint] = {}
    for site in _maskable_site_catalog():
        if site.site_id not in MASKABLE_SITE_IDS:
            continue
        if site.site_id == "subagent_spawn_descriptor":
            sites[site.site_id] = _site_constraint(
                site_id=site.site_id,
                envelope_verbs=envelope_verbs,
                resource_classes=("subagent",),
                max_action_class=max_action_class,
                allowed_action_classes=allowed_action_classes,
                deny_patterns=deny_patterns,
                max_child_scope=remaining_child_scope,
                denied=spawn_denied,
            )
            continue
        sites[site.site_id] = _site_constraint(
            site_id=site.site_id,
            envelope_verbs=envelope_verbs,
            resource_classes=resource_classes,
            max_action_class=max_action_class,
            allowed_action_classes=allowed_action_classes,
            deny_patterns=deny_patterns,
        )

    active_site = str((decode_context or {}).get("site_id") or "")
    maskable_sites = _maskable_site_catalog()
    mask_body = {
        "schema_id": MASK_SPEC_SCHEMA_ID,
        "status": "compilable_target",
        "ir_fingerprint": ir_fingerprint,
        "taxonomy_fingerprint": taxonomy_fingerprint(),
        "sites": {site_id: asdict(constraint) for site_id, constraint in sites.items()},
        "maskable_sites": [asdict(site) for site in maskable_sites],
        "active_site_id": active_site or None,
        "decode_context": dict(decode_context or {}),
        "provider_hints": {
            "implementation": "stub",
            "supported_surfaces": ["structured_output", "logit_mask", "field_mask"],
            "provider_id": str((decode_context or {}).get("provider_id") or "generic"),
        },
        "structured_output_fields": {
            "tool_call.name": "allowed_verbs",
            "tool_call.arguments.effect": "capabilities",
            "claim.label": "authority_envelope.principal.standing_label",
        },
    }
    mask_id = _fingerprint({"ir_fingerprint": ir_fingerprint, "body": mask_body})
    mask_body["mask_id"] = mask_id
    return mask_body


def get_authority_mask(
    ir: dict[str, Any] | Any,
    decode_context: dict[str, Any] | None = None,
) -> MaskSpec:
    """Provider-agnostic mask hook from IR + decode position."""
    lowered = lower_authority_mask(ir, decode_context)
    sites = {
        site_id: MaskConstraint(**constraint)
        for site_id, constraint in lowered.get("sites", {}).items()
    }
    maskable_sites = tuple(
        MaskableSite(**site) for site in lowered.get("maskable_sites", ())
    )
    return MaskSpec(
        mask_id=str(lowered["mask_id"]),
        schema_id=str(lowered["schema_id"]),
        status=str(lowered["status"]),
        ir_fingerprint=str(lowered["ir_fingerprint"]),
        taxonomy_fingerprint=str(lowered["taxonomy_fingerprint"]),
        sites=sites,
        maskable_sites=maskable_sites,
        provider_hints=dict(lowered.get("provider_hints") or {}),
    )
