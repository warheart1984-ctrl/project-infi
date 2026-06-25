#!/usr/bin/env python3
from pathlib import Path
import re, pprint

ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / "tools/governance/_alt17_runtime_bootstrap.py").read_text(encoding="utf-8")
src = src.replace("Alt-17", "Alt-19").replace("alt17", "alt19").replace("BATCH = \"alt17-summon-wave-2026-06\"", "BATCH = \"alt19-summon-wave-2026-06\"")
ORGANS = [
    ("launcher_organ", "platform", "build_launcher_status", "launcher"),
    ("aais_doctor_organ", "platform", "build_aais_doctor_status", "aais-doctor"),
    ("workflow_runtime_organ", "platform", "build_workflow_runtime_status", "workflow-runtime"),
    ("jarvis_console_surface_organ", "platform", "build_jarvis_console_surface_status", "jarvis-console-surface"),
    ("memory_bank_surface_organ", "platform", "build_memory_bank_surface_status", "memory-bank-surface"),
    ("dashboard_surface_organ", "platform", "build_dashboard_surface_status", "dashboard-surface"),
    ("nova_landing_surface_organ", "platform", "build_nova_landing_surface_status", "nova-landing-surface"),
    ("aais_composed_runtime_organ", "platform", "build_aais_composed_runtime_status", "aais-composed-runtime"),
    ("api_gateway_organ", "platform", "build_api_gateway_status", "api-gateway"),
]
organs_repr = "ORGANS = " + pprint.pformat(ORGANS, width=120)
src = re.sub(r"ORGANS = \[.*?\n\]\n\n\ndef gate_script", organs_repr + "\n\n\ndef gate_script", src, count=1, flags=re.S)
(ROOT / "tools/governance/_alt19_runtime_bootstrap.py").write_text(src, encoding="utf-8")
print("ok")
