"""Guest-safe USL lift admission (stdlib only; no networkx / invariant_engine)."""

from __future__ import annotations

from typing import Any

DEFAULT_ADMISSION_VALIDATORS = ("lift_binary_invariant",)


def build_lift_admission_packets_from_dict(
    lifted_model: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build admission packets from serialized lifted_model.json (mirrors governance_bridge)."""
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


def _admission_validators_from_decode(decode_bundle: dict[str, Any]) -> list[str]:
    nodes = (decode_bundle.get("check_graph") or {}).get("nodes") or []
    validators: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("position") or "") != "admission":
            continue
        validator = str(node.get("validator") or "").strip()
        if validator:
            validators.append(validator)
    return validators


def run_lift_admission_from_dict(
    lifted_model: dict[str, Any],
    decode_bundle: dict[str, Any],
) -> dict[str, Any]:
    """Run admission checks without importing invariant_compiler (guest-safe)."""
    normalized_packet, governance_packet = build_lift_admission_packets_from_dict(
        lifted_model
    )

    admission_validators = _admission_validators_from_decode(decode_bundle)
    if not admission_validators:
        admission_validators = list(DEFAULT_ADMISSION_VALIDATORS)

    results: list[dict[str, Any]] = []
    allows = True
    for validator in admission_validators:
        if validator == "lift_binary_invariant":
            blocked: list[str] = []
            for inv in governance_packet.get("lift_invariants") or []:
                if not isinstance(inv, dict):
                    continue
                if str(inv.get("severity") or "") == "block":
                    blocked.append(str(inv.get("invariant_id") or "unknown"))
            allows_lift = len(blocked) == 0
            results.append(
                {
                    "validator": validator,
                    "status": "pass" if allows_lift else "fail",
                    "allows": allows_lift,
                    "details": (
                        "no block-severity lift invariants"
                        if allows_lift
                        else f"blocked invariants: {', '.join(blocked)}"
                    ),
                    "blocked_invariants": blocked,
                }
            )
            allows = allows and allows_lift
        else:
            results.append(
                {
                    "validator": validator,
                    "status": "skipped",
                    "allows": True,
                    "details": "guest_admission: validator not available on guest",
                }
            )

    return {
        "module_id": "aais.invariant_compiler.admission",
        "status": "pass" if allows else "fail",
        "allows": allows,
        "results": results,
    }
