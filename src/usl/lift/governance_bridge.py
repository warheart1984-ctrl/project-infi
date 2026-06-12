"""Bridge lifted binary invariants into Governance IR and admission checks."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from typing import Any

from src.governance_ir import GOVERNANCE_IR_VERSION
from src.invariant_compiler import compile_from_ir, run_admission_checks
from src.usl.lift.types import AAISInvariantRule, ULLiftedModel


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _rule_to_dict(rule: AAISInvariantRule) -> dict[str, Any]:
    return {
        "invariant_id": rule.invariant_id,
        "kind": rule.kind,
        "severity": rule.severity,
        "description": rule.description,
    }


def lift_invariants_to_governance_ir(
    model: ULLiftedModel,
    *,
    law_bundle: dict[str, Any] | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Build a binary-lift Governance IR dict from ULLiftedModel invariants."""
    rules = list(model.invariants.rules)
    hard = tuple(r.invariant_id for r in rules if r.severity == "block")
    conditional = [
        {"name": r.invariant_id, "predicate": "lift_warn"}
        for r in rules
        if r.severity == "warn"
    ]
    effect_buckets = sorted({fx.bucket for fx in model.effects.syscalls if fx.bucket})
    envelope = {
        "principal": {"program_id": model.meta.program_id, "source": "binary_lift"},
        "resources": tuple(
            sorted({r.usl_capability_id for r in model.capabilities.resources})
        ),
        "allowed_verbs": ("observe", "execute"),
        "capabilities": tuple(
            sorted({r.usl_capability_id for r in model.capabilities.resources})
        ),
        "delegation_depth": 0,
        "max_subagent_depth": 0,
    }
    execution_context = {
        "cisiv_stage": "verification",
        "otem_level": "none",
        "otem_boundary": {},
        "subagent_lineage": (),
        "odl_anchor": {},
    }
    body = {
        "ir_version": GOVERNANCE_IR_VERSION,
        "pipeline": "binary_lift",
        "program_id": model.meta.program_id,
        "domain": domain,
        "law_bundle_id": (law_bundle or {}).get("law_id"),
        "authority_envelope": envelope,
        "invariant_set": {
            "hard": list(hard),
            "conditional": conditional,
            "stage_linked": {},
        },
        "execution_context": execution_context,
        "lift_meta": {
            "format": model.meta.format,
            "os_family": model.meta.os_family,
            "architecture": model.meta.architecture,
            "effect_buckets": effect_buckets,
            "syscall_count": len(model.effects.syscalls),
        },
    }
    body["ir_fingerprint"] = _fingerprint(body)
    return body


def build_lift_admission_packets(model: ULLiftedModel) -> tuple[dict[str, Any], dict[str, Any]]:
    """Synthesize normalized + governance packets for lift admission."""
    normalized_packet = {
        "source": "binary_lift",
        "packet_type": "lift_admission",
        "program_id": model.meta.program_id,
        "format": model.meta.format,
        "os_family": model.meta.os_family,
        "architecture": model.meta.architecture,
        "entry_point": model.meta.entry_point,
    }
    governance_packet = {
        "source": "binary_lift",
        "packet_type": "lift_governance",
        "program_id": model.meta.program_id,
        "lift_invariants": [_rule_to_dict(r) for r in model.invariants.rules],
        "effect_surface_summary": {
            "syscall_count": len(model.effects.syscalls),
            "buckets": sorted({fx.bucket for fx in model.effects.syscalls}),
            "allowed_capabilities": [
                r.usl_capability_id for r in model.capabilities.resources
            ],
        },
    }
    return normalized_packet, governance_packet


def compile_lift_governance(
    model: ULLiftedModel,
    *,
    law_bundle: dict[str, Any] | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Compile lift Governance IR into a governance_decode_bundle."""
    ir = lift_invariants_to_governance_ir(model, law_bundle=law_bundle, domain=domain)
    return compile_from_ir(ir)


def build_lift_admission_packets_from_dict(
    lifted_model: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build admission packets from serialized lifted_model.json."""
    meta = lifted_model.get("meta") or {}
    rules = lifted_model.get("invariants", {}).get("rules") or []
    effects = lifted_model.get("effects") or {}
    syscalls = effects.get("syscalls") or []
    capabilities = lifted_model.get("capabilities") or {}
    resources = capabilities.get("resources") or []

    normalized_packet = {
        "source": "binary_lift",
        "packet_type": "lift_admission",
        "program_id": meta.get("program_id"),
        "format": meta.get("format"),
        "os_family": meta.get("os_family"),
        "architecture": meta.get("architecture"),
        "entry_point": meta.get("entry_point"),
    }
    governance_packet = {
        "source": "binary_lift",
        "packet_type": "lift_governance",
        "program_id": meta.get("program_id"),
        "lift_invariants": [
            {
                "invariant_id": r.get("invariant_id"),
                "kind": r.get("kind"),
                "severity": r.get("severity"),
                "description": r.get("description"),
            }
            for r in rules
            if isinstance(r, dict) and r.get("invariant_id")
        ],
        "effect_surface_summary": {
            "syscall_count": len(syscalls),
            "buckets": sorted(
                {
                    str(fx.get("bucket"))
                    for fx in syscalls
                    if isinstance(fx, dict) and fx.get("bucket")
                }
            ),
            "allowed_capabilities": [
                str(r.get("usl_capability_id"))
                for r in resources
                if isinstance(r, dict) and r.get("usl_capability_id")
            ],
        },
    }
    return normalized_packet, governance_packet


def run_lift_admission(
    model: ULLiftedModel,
    decode_bundle: dict[str, Any],
) -> dict[str, Any]:
    """Run admission-position checks for a lifted binary using a decode bundle."""
    normalized_packet, governance_packet = build_lift_admission_packets(model)
    return run_admission_checks(
        normalized_packet,
        governance_packet,
        decode_bundle=decode_bundle,
    )


def run_lift_admission_from_dict(
    lifted_model: dict[str, Any],
    decode_bundle: dict[str, Any],
) -> dict[str, Any]:
    """Run admission checks using serialized lifted_model + decode bundle."""
    normalized_packet, governance_packet = build_lift_admission_packets_from_dict(
        lifted_model
    )
    return run_admission_checks(
        normalized_packet,
        governance_packet,
        decode_bundle=decode_bundle,
    )


def governance_admission_mode() -> str:
    """Return admission mode: compiler (default) or severity-only fallback."""
    mode = os.environ.get("USL_GOVERNANCE_ADMISSION", "compiler").strip().lower()
    if mode not in ("compiler", "severity"):
        return "compiler"
    return mode
