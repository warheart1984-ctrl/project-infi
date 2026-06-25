"""Corridor Loader (CRG_LOADER) — boot-time corridor registry seal."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import UUID

from src.ucr.binary_law_key import validate_law_key
from src.ucr.corridor import (
    AuditPolicy,
    Corridor,
    LaneProfile,
    ResourceBounds,
    build_nova_dev_corridor,
    build_prod_ops_corridor,
)
from src.ucr.corridor_serialize import TrustedCorridorSet, compute_h_corridors
from src.ucr.hash_utils import DEFAULT_HASH_ALG, HashAlg

ERR_NO_CORRIDORS = "ERR_NO_CORRIDORS"
ERR_CORRIDOR_MALFORMED = "ERR_CORRIDOR_MALFORMED"
ERR_LAW_KEY_INVALID = "ERR_LAW_KEY_INVALID"
ERR_CORRIDOR_VERSION_CHAIN = "ERR_CORRIDOR_VERSION_CHAIN"

_TRUSTED_SET: TrustedCorridorSet | None = None
_SEALED = False


class BootResult(str, Enum):
    OK = "OK"
    HALT = "HALT"
    SAFE_MAINTENANCE = "SAFE_MAINTENANCE"


class CorridorLoaderError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class KernelTrustRoot:
    law_spine_hash: bytes
    corridor_hash: bytes
    boot_manifest_hash: bytes
    signing_key_fingerprints: tuple[str, ...]


class CorridorLoader:
    def load_and_seal(
        self,
        registry_path: Path,
        *,
        law_spine_key: int,
        registry_version: int = 1,
        boot_timestamp: str | None = None,
        hash_alg: HashAlg = DEFAULT_HASH_ALG,
    ) -> TrustedCorridorSet:
        corridors = self._discover(registry_path)
        if not corridors:
            raise CorridorLoaderError(ERR_NO_CORRIDORS, f"no corridors under {registry_path}")

        for corridor in corridors:
            self._validate_structure(corridor)
            self._validate_law_keys(corridor, law_spine_key)

        latest = self._resolve_supersession(corridors)
        timestamp = boot_timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        trusted = TrustedCorridorSet.from_corridors(
            latest,
            registry_version=registry_version,
            boot_timestamp=timestamp,
            hash_alg=hash_alg,
        )
        global _TRUSTED_SET, _SEALED
        if _SEALED:
            raise RuntimeError("corridor loader already sealed")
        _TRUSTED_SET = trusted
        _SEALED = True
        return trusted

    def _discover(self, registry_path: Path) -> list[Corridor]:
        if not registry_path.is_dir():
            return [build_nova_dev_corridor(), build_prod_ops_corridor()]

        corridors: list[Corridor] = []
        for entry in sorted(registry_path.glob("corridor_*/manifest.json")):
            corridors.append(self._load_manifest(entry))
        return corridors

    def _load_manifest(self, manifest_path: Path) -> Corridor:
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            lanes = [
                LaneProfile(
                    lane_id=UUID(lane["lane_id"]),
                    name=lane["name"],
                    role=lane["role"],
                    allowed_risk=lane["allowed_risk"],
                    allowed_scopes=list(lane["allowed_scopes"]),
                    law_key=int(lane["law_key"], 16) if isinstance(lane["law_key"], str) else int(lane["law_key"]),
                    resource_bounds=ResourceBounds(**lane["resource_bounds"]),
                )
                for lane in data["lane_profiles"]
            ]
            audit = data["audit_policy"]
            created_at = None
            if data.get("created_at"):
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            return Corridor(
                corridor_id=UUID(data["corridor_id"]),
                name=data["name"],
                owner_id=UUID(data["owner_id"]),
                max_risk=data["max_risk"],
                default_law=int(data["default_law"], 16) if isinstance(data["default_law"], str) else int(data["default_law"]),
                lane_profiles=lanes,
                audit_policy=AuditPolicy(**audit),
                version=int(data["version"]),
                created_at=created_at,
                supersedes=UUID(data["supersedes"]) if data.get("supersedes") else None,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CorridorLoaderError(ERR_CORRIDOR_MALFORMED, str(exc)) from exc

    def _validate_structure(self, corridor: Corridor) -> None:
        required = (
            corridor.corridor_id,
            corridor.name,
            corridor.owner_id,
            corridor.max_risk,
            corridor.default_law,
            corridor.version,
        )
        if not all(required):
            raise CorridorLoaderError(ERR_CORRIDOR_MALFORMED, "missing required corridor fields")
        if not corridor.lane_profiles:
            raise CorridorLoaderError(ERR_CORRIDOR_MALFORMED, "lane_profiles required")

    def _validate_law_keys(self, corridor: Corridor, law_spine_key: int) -> None:
        keys = {corridor.default_law, law_spine_key, *(lane.law_key for lane in corridor.lane_profiles)}
        for key in keys:
            if not validate_law_key(key).ok:
                raise CorridorLoaderError(ERR_LAW_KEY_INVALID, f"invalid law key {key:#x}")
        for lane in corridor.lane_profiles:
            if lane.law_key not in {corridor.default_law, law_spine_key}:
                raise CorridorLoaderError(
                    ERR_LAW_KEY_INVALID,
                    f"lane {lane.lane_id} law_key incompatible with corridor default",
                )

    def _resolve_supersession(self, corridors: list[Corridor]) -> list[Corridor]:
        by_id = {corridor.corridor_id: corridor for corridor in corridors}
        by_name: dict[str, list[Corridor]] = {}
        for corridor in corridors:
            by_name.setdefault(corridor.name, []).append(corridor)

        latest: list[Corridor] = []
        for name, group in by_name.items():
            tips = [c for c in group if not any(other.supersedes == c.corridor_id for other in group)]
            if len(tips) != 1:
                raise CorridorLoaderError(ERR_CORRIDOR_VERSION_CHAIN, f"ambiguous tip for corridor {name}")
            tip = tips[0]
            visited: set[UUID] = set()
            current = tip
            while current.supersedes is not None:
                if current.supersedes in visited:
                    raise CorridorLoaderError(ERR_CORRIDOR_VERSION_CHAIN, "supersession cycle detected")
                visited.add(current.supersedes)
                parent = by_id.get(current.supersedes)
                if parent is None:
                    raise CorridorLoaderError(ERR_CORRIDOR_VERSION_CHAIN, f"missing supersedes target for {current.corridor_id}")
                current = parent
            latest.append(tip)
        return sorted(latest, key=lambda c: str(c.corridor_id))


def get_trusted_corridors() -> TrustedCorridorSet:
    if _TRUSTED_SET is None:
        raise RuntimeError("trusted corridors not sealed")
    return _TRUSTED_SET


def is_sealed() -> bool:
    return _SEALED


def reset_corridor_loader_for_tests() -> None:
    global _TRUSTED_SET, _SEALED
    _TRUSTED_SET = None
    _SEALED = False


def corridor_to_manifest_dict(corridor: Corridor) -> dict:
    return {
        "corridor_id": str(corridor.corridor_id),
        "name": corridor.name,
        "owner_id": str(corridor.owner_id),
        "max_risk": corridor.max_risk,
        "default_law": f"0x{corridor.default_law:032X}",
        "version": corridor.version,
        "created_at": corridor.created_at.isoformat().replace("+00:00", "Z") if corridor.created_at else None,
        "supersedes": str(corridor.supersedes) if corridor.supersedes else None,
        "lane_profiles": [
            {
                **asdict(lane),
                "lane_id": str(lane.lane_id),
                "law_key": f"0x{lane.law_key:032X}",
                "resource_bounds": asdict(lane.resource_bounds),
            }
            for lane in corridor.lane_profiles
        ],
        "audit_policy": asdict(corridor.audit_policy),
    }


def write_corridor_fixture(registry_path: Path, corridor: Corridor) -> None:
    corridor_dir = registry_path / f"corridor_{corridor.corridor_id}"
    corridor_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = corridor_dir / "manifest.json"
    manifest_path.write_text(json.dumps(corridor_to_manifest_dict(corridor), indent=2), encoding="utf-8")
