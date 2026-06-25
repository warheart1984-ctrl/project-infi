"""Dev startup helper — materialize corridor fixture and seal RLS when UCR_* unset."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from src.ucr.corridor import build_nova_dev_corridor, build_prod_ops_corridor
from src.ucr.corridor_loader import reset_corridor_loader_for_tests, write_corridor_fixture
from src.ucr.kernel_boot import BootResult

from runtime_law_spine.runtime_law_spine.constants import (
    DEV_BOOT_TIMESTAMP,
    DEV_KERNEL_STUB,
    DEV_LAW_SPINE_KEY,
)
from runtime_law_spine.runtime_law_spine.gate import RuntimeLawSpineGate

_dev_registry_dir: Path | None = None
_dev_kernel_path: Path | None = None


def _materialize_dev_fixture() -> tuple[Path, Path]:
    global _dev_registry_dir, _dev_kernel_path
    if _dev_registry_dir is not None and _dev_kernel_path is not None:
        return _dev_registry_dir, _dev_kernel_path

    reset_corridor_loader_for_tests()
    base = Path(tempfile.mkdtemp(prefix="rls-dev-"))
    registry = base / "corridors"
    registry.mkdir(parents=True, exist_ok=True)
    write_corridor_fixture(registry, build_nova_dev_corridor())
    write_corridor_fixture(registry, build_prod_ops_corridor())

    kernel_path = base / "kernel-image.stub"
    kernel_path.write_bytes(DEV_KERNEL_STUB)

    _dev_registry_dir = registry
    _dev_kernel_path = kernel_path
    return registry, kernel_path


def ensure_rls_sealed() -> RuntimeLawSpineGate:
    """Run measured boot (env or dev fixture) and enforce RLS gate."""
    registry = os.environ.get("UCR_CORRIDOR_REGISTRY")
    kernel = os.environ.get("UCR_KERNEL_IMAGE")

    if registry and kernel:
        gate = RuntimeLawSpineGate.run_boot()
    else:
        from runtime_law_spine.runtime_law_spine.boot import run_measured_boot

        reg_path, kernel_path = _materialize_dev_fixture()
        result = run_measured_boot(
            registry_path=reg_path,
            kernel_image_path=kernel_path,
            law_spine_key=DEV_LAW_SPINE_KEY,
            boot_timestamp=DEV_BOOT_TIMESTAMP,
        )
        if result.boot_result == BootResult.OK and result.trust_root is not None:
            from src.ucr.trust_root import trust_root_to_receipt_dict

            RuntimeLawSpineGate._instance = RuntimeLawSpineGate(
                sealed=True,
                degraded=False,
                substrate_ok=True,
                halt_reason="",
                trust_root_receipt=trust_root_to_receipt_dict(result.trust_root),
            )
        else:
            detail = result.detail or "dev fixture boot failed"
            RuntimeLawSpineGate._instance = RuntimeLawSpineGate(
                sealed=False,
                degraded=True,
                substrate_ok=False,
                halt_reason=detail,
                trust_root_receipt=None,
            )
        gate = RuntimeLawSpineGate.instance()

    return RuntimeLawSpineGate.require_sealed()
