"""UL lifter orchestrator: UBO → ULLiftedModel."""

from __future__ import annotations

from src.usl.lift.capabilities import lift_capabilities_from_effects
from src.usl.lift.control import lift_control_from_text
from src.usl.lift.data import lift_data_from_meta
from src.usl.lift.effects import lift_effects_from_syscalls
from src.usl.lift.invariants import lift_invariants_from_effects
from src.usl.lift.meta import lift_meta_from_ubo
from src.usl.lift.runtime_shape import lift_runtime_shape_default
from src.usl.lift.types import ULLiftedModel
from src.usl.types import UBO


def lift_machine_code(
    ubo: UBO,
    *,
    artifact_hash: str | None = None,
    source_path: str | None = None,
    build_id: str | None = None,
) -> ULLiftedModel:
    """Lift normalized UBO into ULLiftedModel (P1 ELF x86_64 Linux)."""
    meta = lift_meta_from_ubo(
        ubo,
        artifact_hash=artifact_hash,
        source_path=source_path,
        build_id=build_id,
    )
    control = lift_control_from_text(ubo, meta)
    data = lift_data_from_meta(meta)
    effects = lift_effects_from_syscalls(ubo, control)
    invariants = lift_invariants_from_effects(ubo, effects)
    capabilities = lift_capabilities_from_effects(effects)
    runtime_shape = lift_runtime_shape_default()

    return ULLiftedModel(
        meta=meta,
        control=control,
        data=data,
        effects=effects,
        invariants=invariants,
        capabilities=capabilities,
        runtime_shape=runtime_shape,
    )
