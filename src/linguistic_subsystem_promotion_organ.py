"""Linguistic Subsystem Promotion Subsystem — SSP promotion engine posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LSP-01"
ORGAN_VERSION = "linguistic_subsystem_promotion_organ.v1"


def build_linguistic_subsystem_promotion_status(
    *, root: Path | None = None
) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (root / "src" / "governance_organs" / "promotion_engine.py").is_file()
    alt25_promote = (
        root / "tools" / "governance" / "alt25_promote_mvp.py"
    ).is_file()
    test_alt4 = (root / "tests" / "test_governance_organs_alt4.py").is_file()
    return {
        "linguistic_subsystem_promotion_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};alt25_promote={int(alt25_promote)}"[:128],
        "promotion_engine_present": engine,
        "alt25_promote_script_present": alt25_promote,
        "alt4_promotion_tests_present": test_alt4,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
