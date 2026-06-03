"""Mythic Engineering Translator Subsystem — mythic→engineering translator posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MET-01"
ORGAN_VERSION = "mythic_engineering_translator_organ.v1"


def build_mythic_engineering_translator_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    tool = (root / "tools" / "mythic_engineering_translator.py").is_file()
    tests = (root / "tests" / "test_mythic_engineering_translator.py").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    target = "translate-mythic:" in m_text
    return {
        "mythic_engineering_translator_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"tool={int(tool)};tests={int(tests)};make={int(target)}"[:128],
        "mythic_engineering_translator_present": tool,
        "translator_tests_present": tests,
        "translate_mythic_in_makefile": target,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
