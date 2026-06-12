"""Static Forge emitter: ULLiftedModel → governed image artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.cloud_forge.locality import build_law_bundle, resolve_domain_slice
from src.cloud_forge.types import LawEnvelope
from src.usl.forge.dynamic_emitter import (
    _broker_profile_from_model,
    _capability_bindings_from_model,
    _gate_policy_from_model,
)
from src.usl.lift.governance_bridge import compile_lift_governance
from src.usl.lift.types import ULLiftedModel

LIFTED_ROOT = "opt/cogos/usl-lifted"


@dataclass
class StaticForgeImageRef:
    program_id: str
    rootfs_dir: str
    lifted_dir: str
    artifacts: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def emit_static(
    model: ULLiftedModel,
    *,
    law: LawEnvelope,
    domain: str | None = None,
    rootfs_dir: Path,
) -> StaticForgeImageRef:
    """Write lifted model + law/cap/broker tables under /opt/cogos/usl-lifted/."""
    base = rootfs_dir / LIFTED_ROOT
    base.mkdir(parents=True, exist_ok=True)

    domain_slice = resolve_domain_slice(domain)
    law_bundle = build_law_bundle(law, domain)
    cap_bindings = _capability_bindings_from_model(model)
    broker_profile = _broker_profile_from_model(model)
    gate_policy = _gate_policy_from_model(model)
    governance_decode_bundle = compile_lift_governance(
        model,
        law_bundle=law_bundle,
        domain=domain_slice,
    )

    lattice = {
        "schema": "usl_capability_lattice.v1",
        "program_id": model.meta.program_id,
        "bindings": cap_bindings,
        "domain_slice": domain_slice,
    }

    artifacts: list[str] = []
    writes: list[tuple[str, dict[str, Any]]] = [
        ("lifted_model.json", model.to_dict()),
        ("law_bundle.json", law_bundle),
        ("capability_lattice.json", lattice),
        ("broker_profile.json", broker_profile),
        ("gate_policy.json", gate_policy),
        ("governance_decode_bundle.json", governance_decode_bundle),
    ]
    for name, payload in writes:
        path = base / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifacts.append(str(path.relative_to(rootfs_dir)).replace("\\", "/"))

    return StaticForgeImageRef(
        program_id=model.meta.program_id,
        rootfs_dir=str(rootfs_dir),
        lifted_dir=str(base),
        artifacts=artifacts,
    )
