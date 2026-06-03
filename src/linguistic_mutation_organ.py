"""Linguistic Mutation Subsystem — MP-X linguistic_layer mutation posture."""

# Mythic: Linguistic Mutation Organ
# Engineering: LinguisticMutationEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LMU-01"
ORGAN_VERSION = "linguistic_mutation_organ.v1"


def build_linguistic_mutation_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_mutation_engine.py"
    ).is_file()
    gate_script = (
        root / "tools" / "governance" / "check_linguistic_mutation_gate.py"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-mutation-gate:" in m_text
    return {
        "linguistic_mutation_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};gate_script={int(gate_script)}"[:128],
        "linguistic_mutation_engine_present": engine,
        "linguistic_mutation_gate_script_present": gate_script,
        "linguistic_mutation_gate_in_makefile": gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
