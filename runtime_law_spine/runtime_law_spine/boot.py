"""Measured boot facade for Runtime Law Spine."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from src.ucr.kernel_boot import EarlyBootResult, run_early_boot

from runtime_law_spine.runtime_law_spine.constants import DEV_BOOT_TIMESTAMP, DEV_LAW_SPINE_KEY


@dataclass(frozen=True, slots=True)
class BootPaths:
    registry_path: Path
    kernel_image_path: Path
    law_spine_key: int


def resolve_boot_paths() -> BootPaths:
    registry = os.environ.get("UCR_CORRIDOR_REGISTRY")
    kernel = os.environ.get("UCR_KERNEL_IMAGE")
    law_spine_raw = os.environ.get("UCR_LAW_SPINE")
    if not registry or not kernel:
        raise RuntimeError(
            "UCR_CORRIDOR_REGISTRY and UCR_KERNEL_IMAGE must be set for measured boot"
        )
    law_spine_key = int(law_spine_raw, 0) if law_spine_raw else DEV_LAW_SPINE_KEY
    return BootPaths(
        registry_path=Path(registry),
        kernel_image_path=Path(kernel),
        law_spine_key=law_spine_key,
    )


def run_measured_boot(
    *,
    registry_path: Path | None = None,
    kernel_image_path: Path | None = None,
    law_spine_key: int | None = None,
    boot_timestamp: str = DEV_BOOT_TIMESTAMP,
) -> EarlyBootResult:
    if registry_path is None or kernel_image_path is None:
        paths = resolve_boot_paths()
        registry_path = registry_path or paths.registry_path
        kernel_image_path = kernel_image_path or paths.kernel_image_path
        law_spine_key = law_spine_key if law_spine_key is not None else paths.law_spine_key
    else:
        law_spine_key = law_spine_key if law_spine_key is not None else DEV_LAW_SPINE_KEY

    return run_early_boot(
        registry_path,
        kernel_image_path=kernel_image_path,
        law_spine_key=law_spine_key,
        boot_timestamp=boot_timestamp,
    )
