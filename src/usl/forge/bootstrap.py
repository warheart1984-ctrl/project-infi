"""Bootstrap broker/gate runtime from forge dir or lift-at-startup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.usl.forge.runtime_policy import (
    ForgeRuntimePolicy,
    check_admission,
    load_forge_dir,
)
from src.usl.loaders.elf import guest_from_elf
from src.usl.types import GuestContext


@dataclass
class ForgeBootstrapResult:
    guest: GuestContext
    forge_policy: ForgeRuntimePolicy | None
    lifted_model: dict[str, Any] | None
    artifact_id: str | None


def bootstrap_forge_runtime(
    elf_path: Path | None = None,
    *,
    forge_dir: Path | None = None,
    lift_elf: Path | None = None,
    law_envelope: LawEnvelope | None = None,
    guest: GuestContext | None = None,
) -> ForgeBootstrapResult:
    """
    Load guest + optional forge policy.

    Modes (first match wins):
    - lift_elf: courier lift_and_register (dynamic forge) then admission
    - forge_dir: load static JSON artifacts
    - elf_path only: legacy guest_from_elf without forge policy
    """
    forge_policy: ForgeRuntimePolicy | None = None
    lifted_model: dict[str, Any] | None = None
    artifact_id: str | None = None
    resolved_guest: GuestContext | None = guest

    if lift_elf is not None:
        from src.cloud_forge.types import LawEnvelope
        from src.usl.exo.courier import ExokernelCourier

        law = law_envelope or LawEnvelope(law_id="usl-runtime", law_version="1")
        courier = ExokernelCourier()
        result = courier.lift_and_register_from_path(
            lift_elf,
            forge_mode="dynamic",
            law_envelope=law,
        )
        bundle = result.forge_output
        if not hasattr(bundle, "program_id"):
            raise TypeError("lift_elf requires dynamic forge output")
        forge_policy = ForgeRuntimePolicy.from_dynamic_bundle(bundle)
        lifted_model = result.model.to_dict()
        artifact_id = result.artifact_id
        resolved_guest = result.guest
    elif forge_dir is not None and (forge_dir / "gate_policy.json").is_file():
        forge_policy = load_forge_dir(forge_dir)
        lifted_model = forge_policy.lifted_model
        if resolved_guest is None and elf_path is not None:
            resolved_guest = guest_from_elf(elf_path)
        elif resolved_guest is None:
            raise ValueError(
                "elf_path or guest required when loading USL_FORGE_DIR without lift"
            )
    elif resolved_guest is None and elf_path is not None:
        resolved_guest = guest_from_elf(elf_path)
    elif resolved_guest is None:
        raise ValueError("bootstrap_forge_runtime requires elf_path, forge_dir, or lift_elf")

    assert resolved_guest is not None
    if forge_policy is not None:
        ok, reason = check_admission(forge_policy, lifted_model=lifted_model)
        if not ok:
            raise RuntimeError(reason)
        resolved_guest.profile_id = forge_policy.profile_tier

    return ForgeBootstrapResult(
        guest=resolved_guest,
        forge_policy=forge_policy,
        lifted_model=lifted_model,
        artifact_id=artifact_id,
    )
