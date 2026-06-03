#!/usr/bin/env python3
"""Promote Release 28 Story Forge expansion subsystems to governed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

BATCH = "alt28-summon-wave-2026-06"

ALT28_GENES = (
    "story_forge_launcher_organ",
    "movie_renderer_lane_organ",
    "text_game_to_video_organ",
    "game_front_door_organ",
    "text_to_3d_world_lane_organ",
    "world_pack_lane_organ",
)

ELIGIBILITY = _ROOT / "tools/governance/check_alt28_governed_eligibility.py"


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


def _governed_proof(gene: str) -> str:
    return f"docs/proof/storyforge/{gene.upper()}_GOVERNED_PROOF.md"


def prepare_governed(gene: str, proof: str) -> None:
    data = _load(gene)
    data.setdefault("proof", {})["bundles"] = [proof]
    data.setdefault("activation", {})["batch_id"] = BATCH
    _save(gene, data)


def main() -> int:
    proc = subprocess.run([sys.executable, str(ELIGIBILITY)], cwd=_ROOT, check=False)
    if proc.returncode != 0:
        return 1
    engine = PromotionEngine(_ROOT)
    for gene in ALT28_GENES:
        if (_load(gene).get("identity") or {}).get("stage") == "governed":
            prepare_governed(gene, _governed_proof(gene))
            print(f"[alt28-governed] {gene} already governed (batch stamped)")
            continue
        prepare_governed(gene, _governed_proof(gene))
        decision = engine.evaluate(gene, run_gates=True)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt28-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            return 1
        proof_path = _ROOT / _governed_proof(gene)
        if not proof_path.is_file():
            proof_path.write_text(
                f"# {gene} — Governed Proof\n\nRelease 28 — `{BATCH}`.\n",
                encoding="utf-8",
            )
        print(f"[alt28-governed] {gene} -> governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
