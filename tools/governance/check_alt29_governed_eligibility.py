#!/usr/bin/env python3
"""Release 29 governed eligibility — >=170 governed (Release 29 floor), coherence v1.24."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

BATCH = "alt29-summon-wave-2026-06"


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    reg = GenomeEngine.registry()
    governed = sum(
        1
        for data in reg.genomes.values()
        if (data.get("identity") or {}).get("stage") == "governed"
    )
    if governed < 170:
        errors.append(f"expected at least 170 governed genomes (got {governed})")

    media = reg.genomes.get("media_processor_bridge_organ")
    if not media:
        errors.append("missing genome: media_processor_bridge_organ")
    elif (media.get("identity") or {}).get("stage") != "governed":
        errors.append("media_processor_bridge_organ must be governed")
    elif (media.get("activation") or {}).get("batch_id") != BATCH:
        errors.append("media_processor_bridge_organ batch_id must be alt29")

    fabric = build_coherence_fabric_status(root=root)
    version = fabric.get("operator_cognition_coherence_fabric_version")
    if version != "operator_cognition_coherence_fabric.v1.24":
        errors.append(f"coherence layer must be v1.24 (got {version})")
    if len(fabric.get("story_forge_execution_layer") or []) < 6:
        errors.append("expected 6 story_forge_execution_layer entries")
    if not fabric.get("story_forge_execution_bundle_aligned"):
        errors.append("story_forge_execution_bundle_aligned is false")
    if not fabric.get("integration_universal_bundle_aligned"):
        errors.append("integration_universal_bundle_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt29-governed-gate] FAIL: {err}")
        return 1
    print("[alt29-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
