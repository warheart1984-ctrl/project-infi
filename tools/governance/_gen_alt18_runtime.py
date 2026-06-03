#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / "tools/governance/_alt17_runtime_bootstrap.py").read_text(encoding="utf-8")
src = src.replace("Alt-17", "Alt-18").replace("alt17", "alt18")
ORGANS = [
    ("project_infi_state_machine_organ", "platform", "build_project_infi_state_machine_status", "project-infi-state-machine"),
    ("project_infi_law_organ", "platform", "build_project_infi_law_status", "project-infi-law"),
    ("run_ledger_binding_organ", "platform", "build_run_ledger_binding_status", "run-ledger-binding"),
    ("chat_turn_governance_organ", "platform", "build_chat_turn_governance_status", "chat-turn-governance"),
    ("aais_ul_substrate_organ", "platform", "build_aais_ul_substrate_status", "aais-ul-substrate"),
    ("aris_integration_organ", "platform", "build_aris_integration_status", "aris-integration"),
    ("governance_layer_organ", "platform", "build_governance_layer_status", "governance-layer"),
    ("security_protocol_organ", "platform", "build_security_protocol_status", "security-protocol"),
    ("system_guard_organ", "platform", "build_system_guard_status", "system-guard"),
]
import pprint
organs_repr = "ORGANS = " + pprint.pformat(ORGANS, width=120)
src = re.sub(r"ORGANS = \[.*?\n\]\n\n\ndef gate_script", organs_repr + "\n\n\ndef gate_script", src, count=1, flags=re.S)
(ROOT / "tools/governance/_alt18_runtime_bootstrap.py").write_text(src, encoding="utf-8")
print("ok")
