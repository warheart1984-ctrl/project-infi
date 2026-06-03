"""Patch Verification Organ — read-only verify/preview/apply gate posture."""

# Mythic: Patch Verification Organ
# Engineering: PatchVerificationEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-PV-01"
ORGAN_VERSION = "patch_verification_organ.v1"


def build_patch_verification_status(*, root: Path | None = None) -> dict[str, Any]:
    """Bounded test-oracle and patch-apply gate posture."""
    root = root or Path(__file__).resolve().parents[1]
    oracle = (root / "src" / "test_oracle.py").is_file()
    apply_engine = (root / "src" / "patch_apply_engine.py").is_file()
    review_store = (root / "src" / "patch_review_store.py").is_file()
    apply_gated = True
    summary = (
        f"oracle={oracle};apply={apply_engine};review={review_store};"
        f"apply_gated={apply_gated}"
    )[:128]
    return {
        "patch_verification_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "test_oracle_present": oracle,
        "patch_apply_engine_present": apply_engine,
        "patch_review_store_present": review_store,
        "apply_requires_review": apply_gated,
        "silent_apply_allowed": False,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
