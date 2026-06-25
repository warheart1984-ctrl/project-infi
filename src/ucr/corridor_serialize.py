"""Canonical TrustedCorridorSet serialization for H_CORRIDORS."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.ucr.corridor import Corridor, law_key_to_hex
from src.ucr.hash_utils import DEFAULT_HASH_ALG, HashAlg, digest_bytes, format_measurement


@dataclass(frozen=True, slots=True)
class TrustedCorridorSet:
    corridors: tuple[Corridor, ...]
    law_keys: tuple[int, ...]
    registry_version: int
    boot_timestamp: str
    corridor_hash: str = ""

    @classmethod
    def from_corridors(
        cls,
        corridors: list[Corridor],
        *,
        registry_version: int,
        boot_timestamp: str,
        hash_alg: HashAlg = DEFAULT_HASH_ALG,
    ) -> TrustedCorridorSet:
        law_key_set: set[int] = set()
        for corridor in corridors:
            law_key_set.add(corridor.default_law)
            for lane in corridor.lane_profiles:
                law_key_set.add(lane.law_key)
        trusted = cls(
            corridors=tuple(corridors),
            law_keys=tuple(sorted(law_key_set)),
            registry_version=registry_version,
            boot_timestamp=boot_timestamp,
        )
        h_line = compute_h_corridors(trusted, hash_alg=hash_alg)
        return cls(
            corridors=trusted.corridors,
            law_keys=trusted.law_keys,
            registry_version=trusted.registry_version,
            boot_timestamp=trusted.boot_timestamp,
            corridor_hash=h_line,
        )


def corridor_hash_payload(corridor: Corridor) -> dict[str, Any]:
    return {
        "corridor_id": str(corridor.corridor_id),
        "default_law": law_key_to_hex(corridor.default_law),
        "max_risk": corridor.max_risk,
        "name": corridor.name,
        "owner_id": str(corridor.owner_id),
        "version": corridor.version,
    }


def serialize_trusted_corridor_set(trusted_set: TrustedCorridorSet) -> bytes:
    corridors = sorted(
        [corridor_hash_payload(corridor) for corridor in trusted_set.corridors],
        key=lambda item: item["corridor_id"],
    )
    law_keys = sorted(law_key_to_hex(key) for key in trusted_set.law_keys)
    payload = {
        "corridors": corridors,
        "law_keys": law_keys,
        "registry_version": trusted_set.registry_version,
        "timestamp": trusted_set.boot_timestamp,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_h_corridors(
    trusted_set: TrustedCorridorSet,
    *,
    hash_alg: HashAlg = DEFAULT_HASH_ALG,
) -> str:
    digest = digest_bytes(serialize_trusted_corridor_set(trusted_set), hash_alg)
    return format_measurement(hash_alg, digest.hex())
