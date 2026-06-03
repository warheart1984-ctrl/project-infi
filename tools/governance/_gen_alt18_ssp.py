#!/usr/bin/env python3
"""Generate _alt18_ssp_bootstrap.py from alt17 template."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / "tools/governance/_alt17_ssp_bootstrap.py").read_text(encoding="utf-8")
src = src.replace("Alt-17", "Alt-18").replace("alt17", "alt18")
ORGANS = [
    {
        "gene": "project_infi_state_machine_organ",
        "display": "Project Infi State Machine Organ",
        "module_id": "AAIS-PIS-01",
        "order": 1,
        "parents": ["operator_cognition_coherence_fabric", "ul_lineage_console_organ"],
        "purpose": "Read-only governed cycle state machine posture.",
        "wraps": "src/project_infi_state_machine.py",
        "api": "GET /api/jarvis/project-infi-state-machine/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "project_infi_law_organ",
        "display": "Project Infi Law Organ",
        "module_id": "AAIS-PIL-01",
        "order": 2,
        "parents": ["project_infi_state_machine_organ", "run_ledger_organ"],
        "purpose": "Read-only Project Infi law substrate posture; special_review_only.",
        "wraps": "src/project_infi_law.py",
        "api": "GET /api/jarvis/project-infi-law/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "run_ledger_binding_organ",
        "display": "Run Ledger Binding Organ",
        "module_id": "AAIS-RLB-01",
        "order": 3,
        "parents": ["project_infi_law_organ", "run_ledger_organ"],
        "purpose": "Read-only law-to-run-ledger binding posture.",
        "wraps": "src/run_ledger.py",
        "api": "GET /api/jarvis/run-ledger-binding/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "chat_turn_governance_organ",
        "display": "Chat Turn Governance Organ",
        "module_id": "AAIS-CTG-01",
        "order": 4,
        "parents": ["project_infi_law_organ", "jarvis_operator_organ"],
        "purpose": "Read-only chat-turn UL and admission posture.",
        "wraps": "src/chat_turn_governance.py",
        "api": "GET /api/jarvis/chat-turn-governance/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "aais_ul_substrate_organ",
        "display": "AAIS UL Substrate Organ",
        "module_id": "AAIS-ULS-01",
        "order": 5,
        "parents": ["chat_turn_governance_organ", "cisiv_operator_lineage_console"],
        "purpose": "Read-only UL envelope attachment substrate posture.",
        "wraps": "src/aais_ul_substrate.py",
        "api": "GET /api/jarvis/aais-ul-substrate/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "aris_integration_organ",
        "display": "ARIS Integration Organ",
        "module_id": "AAIS-ARI-01",
        "order": 6,
        "parents": ["project_infi_law_organ", "cognitive_bridge_organ"],
        "purpose": "Read-only embedded ARIS boundary posture.",
        "wraps": "src/aris_integration.py",
        "api": "GET /api/jarvis/aris-integration/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "governance_layer_organ",
        "display": "Governance Layer Organ",
        "module_id": "AAIS-GLY-01",
        "order": 7,
        "parents": ["project_infi_law_organ", "immune_observe_organ"],
        "purpose": "Read-only governance layer and break-glass posture.",
        "wraps": "src/governance_layer.py",
        "api": "GET /api/jarvis/governance-layer/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "security_protocol_organ",
        "display": "Security Protocol Organ",
        "module_id": "AAIS-SPO-01",
        "order": 8,
        "parents": ["governance_layer_organ", "policy_gate_organ"],
        "purpose": "Read-only security protocol core posture.",
        "wraps": "src/security_protocol_core.py",
        "api": "GET /api/jarvis/security-protocol/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "system_guard_organ",
        "display": "System Guard Organ",
        "module_id": "AAIS-SGO-01",
        "order": 9,
        "parents": ["governance_layer_organ", "security_protocol_organ"],
        "purpose": "Read-only system guard control posture.",
        "wraps": "src/system_guard.py",
        "api": "GET /api/jarvis/system-guard/status",
        "proof_subdir": "platform",
    },
]
import json
organs_repr = "ORGANS = " + json.dumps(ORGANS, indent=4).replace("true", "True").replace("false", "False")
# fix json bool - use pprint instead
import pprint
organs_repr = "ORGANS = " + pprint.pformat(ORGANS, width=120)
src = re.sub(r"ORGANS = \[.*?\n\]\n\n\ndef schema_for", organs_repr + "\n\n\ndef schema_for", src, count=1, flags=re.S)
(ROOT / "tools/governance/_alt18_ssp_bootstrap.py").write_text(src, encoding="utf-8")
print("ok")
