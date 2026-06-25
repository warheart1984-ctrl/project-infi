"""Boot manifest formatting and H_BOOT_MANIFEST computation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ucr.hash_utils import DEFAULT_HASH_ALG, HashAlg, digest_bytes, format_measurement, parse_measurement

H_KERNEL_IMAGE_KEY = "H_KERNEL_IMAGE"
H_LAW_SPINE_KEY = "H_LAW_SPINE"
H_CORRIDORS_KEY = "H_CORRIDORS"
H_BOOT_MANIFEST_KEY = "H_BOOT_MANIFEST"


@dataclass(frozen=True, slots=True)
class BootManifest:
    hash_alg: HashAlg
    h_kernel_image: str
    h_law_spine: str
    h_corridors: str
    h_boot_manifest: str
    boot_timestamp: str = ""
    registry_version: int = 1
    raw_without_self: bytes = b""

    def lines(self) -> list[str]:
        rows = [
            f"{H_KERNEL_IMAGE_KEY}={self.h_kernel_image}",
            f"{H_LAW_SPINE_KEY}={self.h_law_spine}",
            f"{H_CORRIDORS_KEY}={self.h_corridors}",
        ]
        if self.boot_timestamp:
            rows.append(f"BOOT_TIMESTAMP={self.boot_timestamp}")
        if self.registry_version:
            rows.append(f"REGISTRY_VERSION={self.registry_version}")
        rows.append(f"{H_BOOT_MANIFEST_KEY}={self.h_boot_manifest}")
        return rows

    def to_bytes(self) -> bytes:
        return "\n".join(self.lines()).encode("utf-8")


def format_h_corridors_line(digest_hex: str, hash_alg: HashAlg = DEFAULT_HASH_ALG) -> str:
    return f"{H_CORRIDORS_KEY}={format_measurement(hash_alg, digest_hex)}"


def build_boot_manifest(
    *,
    h_kernel_image: str,
    h_law_spine: str,
    h_corridors: str,
    boot_timestamp: str,
    registry_version: int = 1,
    hash_alg: HashAlg = DEFAULT_HASH_ALG,
) -> BootManifest:
    pre_lines = [
        f"{H_KERNEL_IMAGE_KEY}={h_kernel_image}",
        f"{H_LAW_SPINE_KEY}={h_law_spine}",
        f"{H_CORRIDORS_KEY}={h_corridors}",
        f"BOOT_TIMESTAMP={boot_timestamp}",
        f"REGISTRY_VERSION={registry_version}",
    ]
    pre_bytes = "\n".join(pre_lines).encode("utf-8")
    h_boot_manifest = format_measurement(hash_alg, digest_bytes(pre_bytes, hash_alg).hex())
    return BootManifest(
        hash_alg=hash_alg,
        h_kernel_image=h_kernel_image,
        h_law_spine=h_law_spine,
        h_corridors=h_corridors,
        h_boot_manifest=h_boot_manifest,
        boot_timestamp=boot_timestamp,
        registry_version=registry_version,
        raw_without_self=pre_bytes,
    )


def write_boot_manifest(path: Path, manifest: BootManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(manifest.to_bytes())


def parse_boot_manifest(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def verify_h_corridors(trusted_line: str, expected_line: str) -> bool:
    return trusted_line == expected_line
