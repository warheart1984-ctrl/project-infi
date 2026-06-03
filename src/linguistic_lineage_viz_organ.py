"""Linguistic Lineage Viz Subsystem — lineage Mermaid export posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LLV-01"
ORGAN_VERSION = "linguistic_lineage_viz_organ.v1"


def build_linguistic_lineage_viz_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    tool = (root / "tools" / "linguistic_lineage_viz.py").is_file()
    tests = (root / "tests" / "test_linguistic_lineage_viz.py").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    target = "linguistic-lineage-viz:" in m_text
    return {
        "linguistic_lineage_viz_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"tool={int(tool)};tests={int(tests)};make={int(target)}"[:128],
        "linguistic_lineage_viz_present": tool,
        "lineage_viz_tests_present": tests,
        "linguistic_lineage_viz_in_makefile": target,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
