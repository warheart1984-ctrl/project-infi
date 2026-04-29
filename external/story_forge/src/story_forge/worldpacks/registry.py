from __future__ import annotations

from dataclasses import dataclass, field

from story_forge.worldpacks.base import WorldPack
from story_forge.worldpacks.brindle_hollow import BRINDLE_HOLLOW_PACK
from story_forge.worldpacks.charming_knife import CHARMING_KNIFE_PACK
from story_forge.worldpacks.dark_fantasy import DARK_FANTASY_PACK
from story_forge.worldpacks.velvet_system import VELVET_SYSTEM_PACK


@dataclass(frozen=True, slots=True)
class WorldPackManifest:
    pack_id: str
    board_id: str
    title: str
    category: str
    tone: str
    premise: str
    start_location_id: str
    tags: tuple[str, ...] = ()
    required_modules: tuple[str, ...] = ()
    optional_modules: tuple[str, ...] = ()
    version: str = "1.0"


@dataclass(frozen=True, slots=True)
class BoardManifest:
    board_id: str
    pack_id: str
    title: str
    category: str
    boot_location_id: str
    required_modules: tuple[str, ...] = ()
    optional_modules: tuple[str, ...] = ()
    version: str = "1.0"


WORLD_PACKS: dict[str, WorldPack] = {
    CHARMING_KNIFE_PACK.pack_id: CHARMING_KNIFE_PACK,
    BRINDLE_HOLLOW_PACK.pack_id: BRINDLE_HOLLOW_PACK,
    DARK_FANTASY_PACK.pack_id: DARK_FANTASY_PACK,
    VELVET_SYSTEM_PACK.pack_id: VELVET_SYSTEM_PACK,
}


def validate_world_pack(world_pack: WorldPack) -> list[str]:
    issues: list[str] = []
    if not world_pack.pack_id:
        issues.append("missing pack_id")
    if not world_pack.name:
        issues.append(f"{world_pack.pack_id or '<unknown>'}: missing name")
    if not world_pack.start_location_id:
        issues.append(f"{world_pack.pack_id or '<unknown>'}: missing start_location_id")
    location_ids = {location.location_id for location in world_pack.locations}
    if world_pack.start_location_id and world_pack.start_location_id not in location_ids:
        issues.append(
            f"{world_pack.pack_id}: start location '{world_pack.start_location_id}' not found in locations"
        )
    if not world_pack.event_templates:
        issues.append(f"{world_pack.pack_id}: missing event templates")
    if not world_pack.ending_templates:
        issues.append(f"{world_pack.pack_id}: missing ending templates")
    return issues


def registry_issues() -> list[str]:
    issues: list[str] = []
    seen_board_ids: set[str] = set()
    for world_pack in WORLD_PACKS.values():
        issues.extend(validate_world_pack(world_pack))
        board_id = board_id_for_pack(world_pack.pack_id)
        if board_id in seen_board_ids:
            issues.append(f"duplicate board id: {board_id}")
        seen_board_ids.add(board_id)
    return issues


def board_id_for_pack(pack_id: str) -> str:
    return f"board.{pack_id}"


def build_world_pack_manifest(world_pack: WorldPack) -> WorldPackManifest:
    required_modules = tuple(
        world_pack.required_modules
        or (
            "worldpack",
            "canon",
            "memory",
            "events",
            "endings",
            "presentation",
        )
    )
    optional_modules = list(world_pack.optional_modules)
    if world_pack.systems and "systems" not in optional_modules:
        optional_modules.append("systems")
    if world_pack.collision_rules and "collisions" not in optional_modules:
        optional_modules.append("collisions")
    if world_pack.action_registry and "actions" not in optional_modules:
        optional_modules.append("actions")
    return WorldPackManifest(
        pack_id=world_pack.pack_id,
        board_id=board_id_for_pack(world_pack.pack_id),
        title=world_pack.name,
        category=world_pack.category,
        tone=world_pack.tone,
        premise=world_pack.premise,
        start_location_id=world_pack.start_location_id,
        tags=tuple(world_pack.tags),
        required_modules=required_modules,
        optional_modules=tuple(optional_modules),
    )


def build_board_manifest(world_pack: WorldPack) -> BoardManifest:
    pack_manifest = build_world_pack_manifest(world_pack)
    return BoardManifest(
        board_id=pack_manifest.board_id,
        pack_id=pack_manifest.pack_id,
        title=pack_manifest.title,
        category=pack_manifest.category,
        boot_location_id=pack_manifest.start_location_id,
        required_modules=pack_manifest.required_modules,
        optional_modules=pack_manifest.optional_modules,
        version=pack_manifest.version,
    )


_WORLD_PACK_MANIFESTS = {
    pack_id: build_world_pack_manifest(world_pack)
    for pack_id, world_pack in WORLD_PACKS.items()
}

_BOARD_MANIFESTS = {
    manifest.board_id: build_board_manifest(WORLD_PACKS[manifest.pack_id])
    for manifest in _WORLD_PACK_MANIFESTS.values()
}


def get_world_pack(pack_id: str) -> WorldPack | None:
    return WORLD_PACKS.get(pack_id)


def list_world_packs() -> list[WorldPack]:
    return [WORLD_PACKS[pack_id] for pack_id in sorted(WORLD_PACKS)]


def get_world_pack_manifest(pack_id: str) -> WorldPackManifest | None:
    return _WORLD_PACK_MANIFESTS.get(pack_id)


def list_world_pack_manifests(*, category: str | None = None) -> list[WorldPackManifest]:
    manifests = [manifest for _, manifest in sorted(_WORLD_PACK_MANIFESTS.items())]
    if category is None:
        return manifests
    normalized = category.strip().lower()
    return [manifest for manifest in manifests if manifest.category.lower() == normalized]


def get_board_manifest(board_id: str) -> BoardManifest | None:
    return _BOARD_MANIFESTS.get(board_id)


def list_board_manifests(*, category: str | None = None) -> list[BoardManifest]:
    manifests = [manifest for _, manifest in sorted(_BOARD_MANIFESTS.items())]
    if category is None:
        return manifests
    normalized = category.strip().lower()
    return [manifest for manifest in manifests if manifest.category.lower() == normalized]
