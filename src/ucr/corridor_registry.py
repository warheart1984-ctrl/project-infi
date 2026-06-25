"""Corridor registry — runtime lookup backed by sealed trusted set."""

from __future__ import annotations

from uuid import UUID

from src.ucr.corridor import Corridor, LaneProfile, build_nova_dev_corridor, build_prod_ops_corridor
from src.ucr.corridor_loader import get_trusted_corridors, is_sealed

_RUNTIME_REGISTRY: dict[UUID, Corridor] = {}
_SEEDED = False


def register_corridor(corridor: Corridor) -> None:
    if is_sealed():
        raise RuntimeError("cannot mutate registry after corridor loader seal")
    _RUNTIME_REGISTRY[corridor.corridor_id] = corridor


def get_corridor(corridor_id: UUID) -> Corridor | None:
    if is_sealed():
        for corridor in get_trusted_corridors().corridors:
            if corridor.corridor_id == corridor_id:
                return corridor
        return None
    return _RUNTIME_REGISTRY.get(corridor_id)


def get_lane(corridor_id: UUID, lane_id: UUID) -> LaneProfile | None:
    corridor = get_corridor(corridor_id)
    if corridor is None:
        return None
    for lane in corridor.lane_profiles:
        if lane.lane_id == lane_id:
            return lane
    return None


def list_corridors() -> tuple[Corridor, ...]:
    if is_sealed():
        return get_trusted_corridors().corridors
    return tuple(_RUNTIME_REGISTRY.values())


def seed_default_corridors() -> None:
    global _SEEDED
    if _SEEDED or is_sealed():
        return
    register_corridor(build_nova_dev_corridor())
    register_corridor(build_prod_ops_corridor())
    _SEEDED = True


def reset_registry() -> None:
    global _SEEDED
    _RUNTIME_REGISTRY.clear()
    _SEEDED = False
