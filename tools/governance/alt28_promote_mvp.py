#!/usr/bin/env python3
"""Stamp Release 28 batch; promote Story Forge expansion subsystems to MVP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

BATCH = "alt28-summon-wave-2026-06"

ALT28_SPECS: dict[str, dict] = {
    "story_forge_launcher_organ": {
        "active_doc": "docs/subsystems/storyforge/STORY_FORGE_LAUNCHER.md",
        "prototype_proof": "docs/proof/storyforge/STORY_FORGE_LAUNCHER_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/storyforge/STORY_FORGE_LAUNCHER_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/story_forge_launcher_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/story_forge_launcher_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/story-forge-launcher/status"},
            {"kind": "gate", "path": "make story-forge-launcher-organ-gate"},
        ],
    },
    "movie_renderer_lane_organ": {
        "active_doc": "docs/subsystems/storyforge/MOVIE_RENDERER_LANE.md",
        "prototype_proof": "docs/proof/storyforge/MOVIE_RENDERER_LANE_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/storyforge/MOVIE_RENDERER_LANE_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/movie_renderer_lane_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/movie_renderer_lane_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/movie-renderer-lane/status"},
            {"kind": "gate", "path": "make movie-renderer-lane-organ-gate"},
        ],
    },
    "text_game_to_video_organ": {
        "active_doc": "docs/subsystems/storyforge/TEXT_GAME_TO_VIDEO.md",
        "prototype_proof": "docs/proof/storyforge/TEXT_GAME_TO_VIDEO_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/storyforge/TEXT_GAME_TO_VIDEO_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/text_game_to_video_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/text_game_to_video_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/text-game-to-video/status"},
            {"kind": "gate", "path": "make text-game-to-video-organ-gate"},
        ],
    },
    "game_front_door_organ": {
        "active_doc": "docs/subsystems/storyforge/GAME_FRONT_DOOR.md",
        "prototype_proof": "docs/proof/storyforge/GAME_FRONT_DOOR_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/storyforge/GAME_FRONT_DOOR_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/game_front_door_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/game_front_door_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/game-front-door/status"},
            {"kind": "gate", "path": "make game-front-door-organ-gate"},
        ],
    },
    "text_to_3d_world_lane_organ": {
        "active_doc": "docs/subsystems/storyforge/TEXT_TO_3D_WORLD_LANE.md",
        "prototype_proof": "docs/proof/storyforge/TEXT_TO_3D_WORLD_LANE_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/storyforge/TEXT_TO_3D_WORLD_LANE_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/text_to_3d_world_lane_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/text_to_3d_world_lane_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/text-to-3d-world-lane/status"},
            {"kind": "gate", "path": "make text-to-3d-world-lane-organ-gate"},
        ],
    },
    "world_pack_lane_organ": {
        "active_doc": "docs/subsystems/storyforge/WORLD_PACK_LANE.md",
        "prototype_proof": "docs/proof/storyforge/WORLD_PACK_LANE_ORGAN_V1_PROOF.md",
        "v1_proof": "docs/proof/storyforge/WORLD_PACK_LANE_ORGAN_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/world_pack_lane_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/world_pack_lane_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/world-pack-lane/status"},
            {"kind": "gate", "path": "make world-pack-lane-organ-gate"},
        ],
    },
}


def _load(gene: str) -> dict:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _save(gene: str, data: dict) -> None:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _stamp_batch(data: dict, order: int) -> None:
    data.setdefault("activation", {})["batch_id"] = BATCH
    data["activation"]["order"] = order
    data["activation"]["notes"] = f"Release 28 wave {order}"


def prepare_prototype(gene: str, spec: dict) -> None:
    data = _load(gene)
    data.setdefault("runtime", {})["surface"] = spec["surface_prototype"]
    data.setdefault("proof", {})["bundles"] = [spec["prototype_proof"]]
    _save(gene, data)


def prepare_mvp(gene: str, spec: dict) -> None:
    data = _load(gene)
    data.setdefault("runtime", {})["surface"] = spec["surface_mvp"]
    data.setdefault("proof", {})["bundles"] = [spec["v1_proof"]]
    data.setdefault("ssp", {})["active_doc"] = spec["active_doc"]
    data.setdefault("ssp", {})["summon_eligible"] = False
    _save(gene, data)


def main() -> int:
    engine = PromotionEngine(_ROOT)
    for order, (gene, spec) in enumerate(ALT28_SPECS.items(), start=1):
        data = _load(gene)
        _stamp_batch(data, order)
        _save(gene, data)
        stage = (data.get("identity") or {}).get("stage")
        if stage in {"mvp", "governed"}:
            print(f"[alt28] {gene} already {stage} (batch stamped)")
            continue
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt28] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt28] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt28] {gene} mvp blocked: {d2.failures}")
            return 1
        d2_apply = engine.apply(d2)
        if not d2_apply.passed:
            print(f"[alt28] {gene} mvp apply failed: {d2_apply.failures}")
            return 1
        print(f"[alt28] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
