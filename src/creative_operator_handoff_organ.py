"""Creative Operator Handoff Subsystem — operator creative lane posture."""

# Mythic: Creative Operator Handoff Organ
# Engineering: CreativeOperatorHandoffBridge
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-COH-01"
ORGAN_VERSION = "creative_operator_handoff_organ.v1"


def build_creative_operator_handoff_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    operator = (root / "src" / "jarvis_operator.py").is_file()
    routing = (root / "src" / "model_routing.py").is_file()
    op_text = (
        (root / "src" / "jarvis_operator.py").read_text(encoding="utf-8")
        if operator
        else ""
    )
    imports_v9 = "v9_runtime" in op_text
    imports_v10 = "v10_runtime" in op_text
    return {
        "creative_operator_handoff_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"operator={int(operator)};v9={int(imports_v9)};v10={int(imports_v10)}"[:128],
        "jarvis_operator_present": operator,
        "model_routing_present": routing,
        "operator_imports_v9_runtime": imports_v9,
        "operator_imports_v10_runtime": imports_v10,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
