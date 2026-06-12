"""Dynamic Forge emitter: ULLiftedModel → broker + law + gate policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.cloud_forge.locality import build_law_bundle, resolve_domain_slice
from src.cloud_forge.types import LawEnvelope
from src.usl.lift.governance_bridge import compile_lift_governance
from src.usl.lift.types import ULLiftedModel


@dataclass
class DynamicForgeBundle:
    program_id: str
    law_bundle: dict[str, Any]
    capability_bindings: dict[str, Any]
    broker_profile: dict[str, Any]
    gate_policy: dict[str, Any]
    domain_slice: dict[str, Any]
    governance_decode_bundle: dict[str, Any] = field(default_factory=dict)
    runtime_shape: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _broker_profile_from_model(model: ULLiftedModel) -> dict[str, Any]:
    """Map static syscall sites to USL capability ids for broker routing."""
    mappings: list[dict[str, Any]] = []
    for fx in model.effects.syscalls:
        cap_id = None
        for res in model.capabilities.resources:
            if res.class_ == fx.bucket or (
                fx.bucket == "fs" and res.usl_capability_id.startswith("fs.")
            ):
                cap_id = res.usl_capability_id
                break
        if cap_id is None and fx.bucket != "unknown":
            cap_id = f"{fx.bucket}.invoke"
        mappings.append(
            {
                "site_vaddr": fx.site_vaddr,
                "syscall_number": fx.syscall_number,
                "syscall_name": fx.syscall_name,
                "bucket": fx.bucket,
                "confidence": fx.confidence,
                "usl_capability_id": cap_id,
            }
        )
    return {
        "program_id": model.meta.program_id,
        "isa": model.meta.architecture,
        "os_family": model.meta.os_family,
        "syscall_mappings": mappings,
    }


def _capability_bindings_from_model(model: ULLiftedModel) -> dict[str, Any]:
    caps = model.capabilities
    return {
        "program_id": model.meta.program_id,
        "ceiling_id": caps.ceiling_id,
        "allowed_capabilities": [r.usl_capability_id for r in caps.resources],
        "authorities": [asdict(a) for a in caps.authorities],
    }


def _gate_policy_from_model(model: ULLiftedModel) -> dict[str, Any]:
    return {
        "program_id": model.meta.program_id,
        "admission_invariants": [
            r.invariant_id
            for r in model.invariants.rules
            if r.severity in ("warn", "block")
        ],
        "all_invariants": [r.invariant_id for r in model.invariants.rules],
    }


def emit_dynamic(
    model: ULLiftedModel,
    *,
    law: LawEnvelope,
    domain: str | None = None,
) -> DynamicForgeBundle:
    """Build dynamic-world governance bundle without re-emitting machine code."""
    domain_slice = resolve_domain_slice(domain)
    law_bundle = build_law_bundle(law, domain)
    governance_decode_bundle = compile_lift_governance(
        model,
        law_bundle=law_bundle,
        domain=domain_slice,
    )
    return DynamicForgeBundle(
        program_id=model.meta.program_id,
        law_bundle=law_bundle,
        capability_bindings=_capability_bindings_from_model(model),
        broker_profile=_broker_profile_from_model(model),
        gate_policy=_gate_policy_from_model(model),
        domain_slice=domain_slice,
        governance_decode_bundle=governance_decode_bundle,
        runtime_shape=model.runtime_shape.to_dict()
        if hasattr(model.runtime_shape, "to_dict")
        else asdict(model.runtime_shape),
    )
