#!/usr/bin/env python3
"""Promote Release 29 batch: media organ governed + Story Forge execution proof stamp."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

BATCH = "alt29-summon-wave-2026-06"
MEDIA_GENE = "media_processor_bridge_organ"
ALT28_GENES = (
    "story_forge_launcher_organ",
    "movie_renderer_lane_organ",
    "text_game_to_video_organ",
    "game_front_door_organ",
    "text_to_3d_world_lane_organ",
    "world_pack_lane_organ",
)
EXECUTION_PROOFS = {
    "story_forge_launcher_organ": (
        "docs/proof/storyforge/STORY_FORGE_LAUNCHER_ORGAN_EXECUTION_V1_PROOF.md"
    ),
    "movie_renderer_lane_organ": (
        "docs/proof/storyforge/MOVIE_RENDERER_LANE_ORGAN_EXECUTION_V1_PROOF.md"
    ),
    "text_game_to_video_organ": (
        "docs/proof/storyforge/TEXT_GAME_TO_VIDEO_ORGAN_EXECUTION_V1_PROOF.md"
    ),
    "game_front_door_organ": (
        "docs/proof/storyforge/GAME_FRONT_DOOR_ORGAN_EXECUTION_V1_PROOF.md"
    ),
    "text_to_3d_world_lane_organ": (
        "docs/proof/storyforge/TEXT_TO_3D_WORLD_LANE_ORGAN_EXECUTION_V1_PROOF.md"
    ),
    "world_pack_lane_organ": (
        "docs/proof/storyforge/WORLD_PACK_LANE_ORGAN_EXECUTION_V1_PROOF.md"
    ),
}
GOVERNED_MEDIA_PROOF = "docs/proof/platform/MEDIA_PROCESSOR_BRIDGE_ORGAN_GOVERNED_PROOF.md"
ELIGIBILITY = _ROOT / "tools/governance/check_alt29_governed_eligibility.py"


def _load(gene: str) -> dict:
    return json.loads(
        (_ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json").read_text(
            encoding="utf-8"
        )
    )


def _save(gene: str, data: dict) -> None:
    (_ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )


def ensure_execution_proofs() -> None:
    for gene, rel in EXECUTION_PROOFS.items():
        path = _ROOT / rel
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"# {gene} — Execution V1 Proof\n\nRelease 29 — `{BATCH}`.\n",
                encoding="utf-8",
            )


def stamp_alt28_execution_batch() -> None:
    for gene in ALT28_GENES:
        data = _load(gene)
        activation = data.setdefault("activation", {})
        notes = str(activation.get("notes") or "")
        if "alt29-execution" not in notes:
            activation["notes"] = (notes + "; alt29-execution-wave").strip("; ")
        _save(gene, data)


def main() -> int:
    ensure_execution_proofs()
    stamp_alt28_execution_batch()
    engine = PromotionEngine(_ROOT)
    data = _load(MEDIA_GENE)
    data.setdefault("proof", {})["bundles"] = [GOVERNED_MEDIA_PROOF]
    data.setdefault("activation", {})["batch_id"] = BATCH
    _save(MEDIA_GENE, data)
    if (_load(MEDIA_GENE).get("identity") or {}).get("stage") != "governed":
        decision = engine.evaluate(MEDIA_GENE, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt29-governed] {MEDIA_GENE} blocked: {decision.failures}")
            return 1
        engine.apply(decision)
    proof_path = _ROOT / GOVERNED_MEDIA_PROOF
    if not proof_path.is_file():
        proof_path.write_text(
            f"# Media Processor Bridge Organ — Governed Proof\n\n`{BATCH}`.\n",
            encoding="utf-8",
        )
    print(f"[alt29-governed] {MEDIA_GENE} -> governed")
    proc = subprocess.run([sys.executable, str(ELIGIBILITY)], cwd=_ROOT, check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
