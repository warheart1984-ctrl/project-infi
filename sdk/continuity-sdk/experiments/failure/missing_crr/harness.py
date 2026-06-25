"""Missing CRR-1 demo — continuity collapse without calibration preservation."""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    # Without CRR-1 lineage, assimilation cannot meet threshold with realistic pre-error
    from src.crk1.caa1_assimilation import (
        AssimilationContext,
        JudgmentQualitySample,
        build_caa1_receipt,
    )

    pre = JudgmentQualitySample("s2", "physics.fall", 0.7, False)
    post = JudgmentQualitySample("s2", "physics.fall", 0.65, False)  # no CRR replay benefit
    receipt = build_caa1_receipt(
        AssimilationContext(
            steward_id="s2",
            original_participant_ids=["s1"],
            crr_hash="0" * 64,
            clg_hash="0" * 64,
            contradiction_class="physics.fall",
            pre_sample=pre,
            post_sample=post,
        )
    )
    return {
        "question": "Does continuity collapse without CRR-1?",
        "passed": not receipt["continuity_passed"],
        "assimilation_delta": receipt["assimilation_delta"],
    }
