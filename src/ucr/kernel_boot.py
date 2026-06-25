"""Early kernel boot orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ucr.boot_manifest import BootManifest, build_boot_manifest
from src.ucr.corridor_loader import BootResult, CorridorLoader, CorridorLoaderError, get_trusted_corridors, is_sealed
from src.ucr.hash_utils import DEFAULT_HASH_ALG, HashAlg, digest_bytes, format_measurement
from src.ucr.law_spine_pack import compute_h_law_spine, load_law_spine_modules
from src.ucr.trust_root import TrustRoot, build_trust_root, get_trust_root, is_trust_root_sealed, seal_trust_root, to_ucr_context


@dataclass(frozen=True, slots=True)
class EarlyBootResult:
    boot_result: BootResult
    trust_root: TrustRoot | None
    manifest: BootManifest | None
    detail: str = ""


def run_early_boot(
    registry_path: Path,
    *,
    kernel_image_path: Path | None = None,
    law_spine_path: Path | None = None,
    boot_timestamp: str = "2026-06-18T10:00:00Z",
    registry_version: int = 1,
    law_spine_key: int = 0x010229CAFF000000000000005532534F,
    hash_alg: HashAlg = DEFAULT_HASH_ALG,
) -> EarlyBootResult:
    try:
        kernel_bytes = _load_kernel_image(kernel_image_path)
        h_kernel_image = format_measurement(hash_alg, digest_bytes(kernel_bytes, hash_alg).hex())

        modules = load_law_spine_modules(law_spine_path)
        h_law_spine = compute_h_law_spine(modules, hash_alg=hash_alg)

        loader = CorridorLoader()
        trusted = loader.load_and_seal(
            registry_path,
            law_spine_key=law_spine_key,
            registry_version=registry_version,
            boot_timestamp=boot_timestamp,
            hash_alg=hash_alg,
        )
        h_corridors = trusted.corridor_hash

        manifest = build_boot_manifest(
            h_kernel_image=h_kernel_image,
            h_law_spine=h_law_spine,
            h_corridors=h_corridors,
            boot_timestamp=boot_timestamp,
            registry_version=registry_version,
            hash_alg=hash_alg,
        )
        trust_root = build_trust_root(manifest)
        seal_trust_root(trust_root)
        return EarlyBootResult(boot_result=BootResult.OK, trust_root=trust_root, manifest=manifest)
    except CorridorLoaderError as exc:
        return EarlyBootResult(boot_result=BootResult.HALT, trust_root=None, manifest=None, detail=str(exc))


def get_trust_root_syscall() -> dict[str, str]:
    trust_root = get_trust_root()
    context = to_ucr_context(trust_root)
    return {
        "hash_alg": context.hash_alg,
        "h_kernel_image": trust_root.h_kernel_image,
        "h_law_spine": context.h_law_spine,
        "h_corridors": context.h_corridors,
        "h_boot_manifest": trust_root.h_boot_manifest,
        "h_trust_root": context.h_trust_root,
        "corridors_sealed": str(is_sealed()),
        "trust_root_sealed": str(is_trust_root_sealed()),
    }


def _load_kernel_image(kernel_image_path: Path | None) -> bytes:
    if kernel_image_path and kernel_image_path.is_file():
        return kernel_image_path.read_bytes()
    return b"aaes-kernel-image-stub-v0.1"
