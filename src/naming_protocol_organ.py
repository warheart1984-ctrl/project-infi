"""Naming Protocol Subsystem — Wave 0 naming lint posture."""

# Mythic: Naming Protocol Organ
# Engineering: NamingProtocolEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-NPR-01"
ORGAN_VERSION = "naming_protocol_organ.v1"


def build_naming_protocol_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    lint = (root / "tools" / "naming_protocol_lint.py").is_file()
    contract = (
        root / "docs" / "contracts" / "AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    naming_gate = "naming-gate:" in m_text
    return {
        "naming_protocol_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"lint={int(lint)};contract={int(contract)};gate={int(naming_gate)}"[:128],
        "naming_protocol_lint_present": lint,
        "naming_protocol_contract_present": contract,
        "naming_gate_in_makefile": naming_gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
