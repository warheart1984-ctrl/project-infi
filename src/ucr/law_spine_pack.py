"""Canonical law spine bundle packing for H_LAW_SPINE."""

from __future__ import annotations

from pathlib import Path

from src.ucr.hash_utils import DEFAULT_HASH_ALG, HashAlg, digest_bytes, format_measurement

LAW_MODULE_IDS = (
    "LAW_CONS_v1",
    "LAW_SPINE_UCR_v0.1",
    "BLK_UCR_V0",
)


def canonical_pack(modules: dict[str, bytes]) -> bytes:
    parts: list[bytes] = []
    for module_id in sorted(modules.keys()):
        content = modules[module_id]
        parts.append(module_id.encode("utf-8"))
        parts.append(b"\x00")
        parts.append(len(content).to_bytes(4, "big"))
        parts.append(content)
    return b"".join(parts)


def load_law_spine_modules(base_path: Path | None = None) -> dict[str, bytes]:
    root = base_path or Path("docs/contracts")
    modules: dict[str, bytes] = {}
    mapping = {
        "LAW_CONS_v1": root / "AAES_OS_V1_FORMAL_SPEC.md",
        "LAW_SPINE_UCR_v0.1": root / "AAES-OS_LAW_SPINE_UCR_v0.1.md",
        "BLK_UCR_V0": root / "BLK_UCR_V0.md",
    }
    for module_id, path in mapping.items():
        if path.is_file():
            modules[module_id] = path.read_bytes()
        elif module_id == "BLK_UCR_V0":
            modules[module_id] = b"BLK_UCR_V0 canonical law key specification"
        elif module_id == "LAW_SPINE_UCR_v0.1":
            modules[module_id] = b"AAES-OS Law Spine UCR v0.1 placeholder"
        else:
            modules[module_id] = path.name.encode("utf-8")
    return modules


def compute_h_law_spine(
    modules: dict[str, bytes] | None = None,
    *,
    base_path: Path | None = None,
    hash_alg: HashAlg = DEFAULT_HASH_ALG,
) -> str:
    bundle = canonical_pack(modules or load_law_spine_modules(base_path))
    return format_measurement(hash_alg, digest_bytes(bundle, hash_alg).hex())
