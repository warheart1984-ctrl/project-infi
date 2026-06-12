"""Load forge artifacts and evaluate lifted governance at broker/gate runtime."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.usl.forge.dynamic_emitter import DynamicForgeBundle

from src.usl.law.default_policy import (
    ALLOW,
    CEILING_CAPABILITIES,
    DENY,
    evaluate_capability as default_evaluate_capability,
)
from src.usl.law.default_policy import LawDecision
from src.usl.types import CapabilityRequest


def _governance_admission_mode() -> str:
    """Admission mode without importing governance_bridge (avoids networkx on guest)."""
    mode = os.environ.get("USL_GOVERNANCE_ADMISSION", "compiler").strip().lower()
    if mode not in ("compiler", "severity"):
        return "compiler"
    return mode


def _bundle_for_capability(capability_id: str) -> str | None:
    """Return the first ceiling bundle id that contains capability_id."""
    for bundle_id, caps in CEILING_CAPABILITIES.items():
        if capability_id in caps:
            return bundle_id
    return None


@dataclass
class ForgeRuntimePolicy:
    """Runtime view of a dynamic or static forge bundle."""

    program_id: str
    profile_tier: str
    allowed_capabilities: frozenset[str]
    gate_policy: dict[str, Any]
    broker_profile: dict[str, Any]
    capability_bindings: dict[str, Any]
    lifted_model: dict[str, Any] | None = None
    law_bundle: dict[str, Any] | None = None
    governance_decode_bundle: dict[str, Any] | None = None
    _invariant_severity: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dynamic_bundle(cls, bundle: DynamicForgeBundle) -> ForgeRuntimePolicy:
        bindings = bundle.capability_bindings
        tier = bindings.get("ceiling_id") or "daily-driver"
        allowed = frozenset(bindings.get("allowed_capabilities") or [])
        return cls(
            program_id=bundle.program_id,
            profile_tier=tier,
            allowed_capabilities=allowed,
            gate_policy=bundle.gate_policy,
            broker_profile=bundle.broker_profile,
            capability_bindings=bindings,
            law_bundle=bundle.law_bundle,
            governance_decode_bundle=bundle.governance_decode_bundle or None,
        )

    @classmethod
    def from_forge_dir(cls, forge_dir: Path) -> ForgeRuntimePolicy:
        return load_forge_dir(forge_dir)


def load_forge_dir(path: Path) -> ForgeRuntimePolicy:
    """Deserialize static emitter JSON under opt/cogos/usl-lifted."""
    base = Path(path)
    gate_path = base / "gate_policy.json"
    broker_path = base / "broker_profile.json"
    lattice_path = base / "capability_lattice.json"
    model_path = base / "lifted_model.json"
    law_path = base / "law_bundle.json"

    if not gate_path.is_file():
        raise FileNotFoundError(f"missing gate_policy.json under {base}")

    gate_policy = json.loads(gate_path.read_text(encoding="utf-8"))
    broker_profile = (
        json.loads(broker_path.read_text(encoding="utf-8"))
        if broker_path.is_file()
        else {}
    )
    lattice = (
        json.loads(lattice_path.read_text(encoding="utf-8"))
        if lattice_path.is_file()
        else {}
    )
    bindings = lattice.get("bindings") or {}
    if not bindings and (base / "capability_bindings.json").is_file():
        bindings = json.loads(
            (base / "capability_bindings.json").read_text(encoding="utf-8")
        )

    lifted_model = (
        json.loads(model_path.read_text(encoding="utf-8"))
        if model_path.is_file()
        else None
    )
    law_bundle = (
        json.loads(law_path.read_text(encoding="utf-8"))
        if law_path.is_file()
        else None
    )
    governance_path = base / "governance_decode_bundle.json"
    governance_decode_bundle = (
        json.loads(governance_path.read_text(encoding="utf-8"))
        if governance_path.is_file()
        else None
    )

    program_id = (
        gate_policy.get("program_id")
        or bindings.get("program_id")
        or broker_profile.get("program_id")
        or "unknown"
    )
    tier = bindings.get("ceiling_id") or "daily-driver"
    allowed = frozenset(bindings.get("allowed_capabilities") or [])

    severity_map: dict[str, str] = {}
    if lifted_model:
        for rule in lifted_model.get("invariants", {}).get("rules") or []:
            if isinstance(rule, dict) and rule.get("invariant_id"):
                severity_map[rule["invariant_id"]] = str(
                    rule.get("severity") or "info"
                )

    return ForgeRuntimePolicy(
        program_id=program_id,
        profile_tier=tier,
        allowed_capabilities=allowed,
        gate_policy=gate_policy,
        broker_profile=broker_profile,
        capability_bindings=bindings,
        lifted_model=lifted_model,
        law_bundle=law_bundle,
        governance_decode_bundle=governance_decode_bundle,
        _invariant_severity=severity_map,
    )


def _check_admission_severity_map(
    policy: ForgeRuntimePolicy,
    model: dict[str, Any] | None,
) -> tuple[bool, str]:
    """Legacy admission path using gate_policy admission_invariants + severities."""
    severity_map = dict(policy._invariant_severity)
    if model:
        for rule in model.get("invariants", {}).get("rules") or []:
            if isinstance(rule, dict) and rule.get("invariant_id"):
                severity_map[rule["invariant_id"]] = str(
                    rule.get("severity") or "info"
                )

    for inv_id in policy.gate_policy.get("admission_invariants") or []:
        sev = severity_map.get(inv_id, "warn")
        if sev == "block":
            return False, f"admission blocked: invariant {inv_id}"
    return True, "admitted"


def check_admission(
    policy: ForgeRuntimePolicy,
    *,
    lifted_model: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Refuse guest startup when admission invariants fail (compiler or severity path)."""
    model = lifted_model or policy.lifted_model
    mode = _governance_admission_mode()
    bundle = policy.governance_decode_bundle

    if mode == "compiler" and bundle and model:
        from src.usl.lift.guest_admission import run_lift_admission_from_dict

        outcome = run_lift_admission_from_dict(model, bundle)
        if not outcome.get("allows", True):
            blocked: list[str] = []
            for r in outcome.get("results") or []:
                if not isinstance(r, dict):
                    continue
                if r.get("validator") == "lift_binary_invariant":
                    blocked = list(r.get("blocked_invariants") or [])
                    break
            if blocked:
                return False, f"admission blocked: invariants {blocked}"
            return False, "admission blocked: lift_binary_invariant"
        return True, "admitted"

    return _check_admission_severity_map(policy, model)


def resolve_syscall_capability(
    policy: ForgeRuntimePolicy,
    syscall_number: int,
) -> str | None:
    """Map a syscall number to a USL capability id via broker_profile."""
    for mapping in policy.broker_profile.get("syscall_mappings") or []:
        if not isinstance(mapping, dict):
            continue
        num = mapping.get("syscall_number")
        if num is None:
            continue
        try:
            if int(num) != int(syscall_number):
                continue
        except (TypeError, ValueError):
            continue
        confidence = str(mapping.get("confidence") or "unknown")
        if confidence == "unknown":
            return None
        cap_id = mapping.get("usl_capability_id")
        return str(cap_id) if cap_id else None
    return None


def evaluate_capability(
    request: CapabilityRequest,
    policy: ForgeRuntimePolicy,
) -> LawDecision:
    """Intersect lifted allow-list with default profile ceilings."""
    cap_id = request.capability_id
    policy_id = f"policy:forge:{policy.program_id}"
    lawbook_id = "lawbook:usl-v1"

    if policy.allowed_capabilities and cap_id not in policy.allowed_capabilities:
        return LawDecision(
            decision=DENY,
            policy_id=policy_id,
            lawbook_id=lawbook_id,
            decision_reason="lifted_allowlist",
            decision_detail=(
                f"capability {cap_id} not in lifted allow-list for {policy.program_id}"
            ),
        )

    tier = policy.profile_tier
    guest = replace(request.guest, profile_id=tier)
    req = replace(request, guest=guest)
    decision = default_evaluate_capability(req)
    if decision.decision != ALLOW:
        return replace(
            decision,
            policy_id=policy_id,
            decision_detail=f"forge:{decision.decision_detail}",
        )

    bundle = _bundle_for_capability(cap_id)
    if bundle and request.ceiling_id and request.ceiling_id != bundle:
        if cap_id not in CEILING_CAPABILITIES.get(request.ceiling_id, set()):
            return LawDecision(
                decision=DENY,
                policy_id=policy_id,
                lawbook_id=lawbook_id,
                decision_reason="ceiling_mismatch",
                decision_detail=(
                    f"capability {cap_id} not in requested ceiling {request.ceiling_id}"
                ),
            )

    return replace(
        decision,
        policy_id=policy_id,
        decision_detail=f"forge:{decision.decision_detail}",
    )
