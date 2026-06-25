"""Trust Root measurement chain and sealed boot state."""

from __future__ import annotations

from dataclasses import dataclass

from src.ucr.boot_manifest import BootManifest
from src.ucr.hash_utils import DEFAULT_HASH_ALG, HashAlg, digest_bytes, format_measurement, measurement_to_raw_bytes

TRUST_ROOT_DOMAIN = b"AAES-TRUST-ROOT-v1\x00"

_SEALED_TRUST_ROOT: TrustRoot | None = None


@dataclass(frozen=True, slots=True)
class TrustRoot:
    hash_alg: HashAlg
    h_kernel_image: str
    h_law_spine: str
    h_corridors: str
    h_boot_manifest: str
    h_trust_root: str

    @property
    def corridor_hash(self) -> str:
        return self.h_corridors


@dataclass(frozen=True, slots=True)
class UCRTrustContext:
    hash_alg: str
    h_law_spine: str
    h_corridors: str
    h_trust_root: str


def compute_h_trust_root(
    *,
    h_kernel_image: str,
    h_law_spine: str,
    h_corridors: str,
    h_boot_manifest: str,
    hash_alg: HashAlg = DEFAULT_HASH_ALG,
) -> str:
    payload = TRUST_ROOT_DOMAIN + b"".join(
        [
            measurement_to_raw_bytes(h_kernel_image),
            measurement_to_raw_bytes(h_law_spine),
            measurement_to_raw_bytes(h_corridors),
            measurement_to_raw_bytes(h_boot_manifest),
        ]
    )
    return format_measurement(hash_alg, digest_bytes(payload, hash_alg).hex())


def build_trust_root(manifest: BootManifest) -> TrustRoot:
    h_trust_root = compute_h_trust_root(
        h_kernel_image=manifest.h_kernel_image,
        h_law_spine=manifest.h_law_spine,
        h_corridors=manifest.h_corridors,
        h_boot_manifest=manifest.h_boot_manifest,
        hash_alg=manifest.hash_alg,
    )
    return TrustRoot(
        hash_alg=manifest.hash_alg,
        h_kernel_image=manifest.h_kernel_image,
        h_law_spine=manifest.h_law_spine,
        h_corridors=manifest.h_corridors,
        h_boot_manifest=manifest.h_boot_manifest,
        h_trust_root=h_trust_root,
    )


def trust_root_to_receipt_dict(trust_root: TrustRoot) -> dict[str, str]:
    """JSON-serializable boot receipt for RLS gate and attestation artifacts."""
    return {
        "hash_alg": trust_root.hash_alg,
        "h_kernel_image": trust_root.h_kernel_image,
        "h_law_spine": trust_root.h_law_spine,
        "h_corridors": trust_root.h_corridors,
        "h_boot_manifest": trust_root.h_boot_manifest,
        "h_trust_root": trust_root.h_trust_root,
    }


def to_ucr_context(trust_root: TrustRoot) -> UCRTrustContext:
    return UCRTrustContext(
        hash_alg=trust_root.hash_alg,
        h_law_spine=trust_root.h_law_spine,
        h_corridors=trust_root.h_corridors,
        h_trust_root=trust_root.h_trust_root,
    )


def seal_trust_root(trust_root: TrustRoot) -> None:
    global _SEALED_TRUST_ROOT
    if _SEALED_TRUST_ROOT is not None:
        raise RuntimeError("trust root already sealed")
    _SEALED_TRUST_ROOT = trust_root


def get_trust_root() -> TrustRoot:
    if _SEALED_TRUST_ROOT is None:
        raise RuntimeError("trust root not sealed")
    return _SEALED_TRUST_ROOT


def is_trust_root_sealed() -> bool:
    return _SEALED_TRUST_ROOT is not None


def reset_trust_root_for_tests() -> None:
    global _SEALED_TRUST_ROOT
    _SEALED_TRUST_ROOT = None
