#!/usr/bin/env python3
from pathlib import Path
import re, pprint

ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / "tools/governance/_alt17_ssp_bootstrap.py").read_text(encoding="utf-8")
src = src.replace("Alt-17", "Alt-19").replace("alt17", "alt19").replace("BATCH = \"alt17-summon-wave-2026-06\"", "BATCH = \"alt19-summon-wave-2026-06\"")
ORGANS = [
    {"gene": "launcher_organ", "display": "Launcher Organ", "module_id": "AAIS-LCH-01", "order": 1, "parents": ["workflow_shell_organ", "capability_service_bridge"], "purpose": "Read-only AAIS launcher package posture.", "wraps": "aais/launcher.py", "api": "GET /api/jarvis/launcher/status", "proof_subdir": "platform"},
    {"gene": "aais_doctor_organ", "display": "AAIS Doctor Organ", "module_id": "AAIS-DOC-01", "order": 2, "parents": ["launcher_organ"], "purpose": "Read-only aais doctor readiness posture.", "wraps": "aais/__main__.py", "api": "GET /api/jarvis/aais-doctor/status", "proof_subdir": "platform"},
    {"gene": "workflow_runtime_organ", "display": "Workflow Runtime Organ", "module_id": "AAIS-WRT-01", "order": 3, "parents": ["workflow_shell_organ", "launcher_organ"], "purpose": "Read-only app/workflow_runtime posture (distinct from workflow_shell_organ).", "wraps": "app/workflow_runtime.py", "api": "GET /api/jarvis/workflow-runtime/status", "proof_subdir": "platform"},
    {"gene": "jarvis_console_surface_organ", "display": "Jarvis Console Surface Organ", "module_id": "AAIS-JCS-01", "order": 4, "parents": ["jarvis_operator_organ"], "purpose": "Read-only Jarvis Console UI binding posture.", "wraps": "frontend/src/pages/JarvisConsole.jsx", "api": "GET /api/jarvis/jarvis-console-surface/status", "proof_subdir": "platform"},
    {"gene": "memory_bank_surface_organ", "display": "Memory Bank Surface Organ", "module_id": "AAIS-MBS-01", "order": 5, "parents": ["jarvis_memory_board", "jarvis_console_surface_organ"], "purpose": "Read-only Memory Bank UI binding posture.", "wraps": "frontend/src/pages/MemoryBank.jsx", "api": "GET /api/jarvis/memory-bank-surface/status", "proof_subdir": "platform"},
    {"gene": "dashboard_surface_organ", "display": "Dashboard Surface Organ", "module_id": "AAIS-DBS-01", "order": 6, "parents": ["governance_layer_organ", "jarvis_console_surface_organ"], "purpose": "Read-only Dashboard governance views posture.", "wraps": "frontend/src/pages/Dashboard.jsx", "api": "GET /api/jarvis/dashboard-surface/status", "proof_subdir": "platform"},
    {"gene": "nova_landing_surface_organ", "display": "Nova Landing Surface Organ", "module_id": "AAIS-NLS-01", "order": 7, "parents": ["nova_face_organ", "jarvis_console_surface_organ"], "purpose": "Read-only Nova landing surface posture.", "wraps": "frontend/src/pages/NovaLandingPage.jsx", "api": "GET /api/jarvis/nova-landing-surface/status", "proof_subdir": "platform"},
    {"gene": "aais_composed_runtime_organ", "display": "AAIS Composed Runtime Organ", "module_id": "AAIS-ACR-01", "order": 8, "parents": ["jarvis_operator_organ", "governance_layer_organ"], "purpose": "Read-only composed runtime posture.", "wraps": "src/aais_composed_runtime.py", "api": "GET /api/jarvis/aais-composed-runtime/status", "proof_subdir": "platform"},
    {"gene": "api_gateway_organ", "display": "API Gateway Organ", "module_id": "AAIS-AGW-01", "order": 9, "parents": ["jarvis_operator_organ", "capability_service_bridge"], "purpose": "Read-only bounded api.py ingress posture.", "wraps": "src/api.py", "api": "GET /api/jarvis/api-gateway/status", "proof_subdir": "platform"},
]
organs_repr = "ORGANS = " + pprint.pformat(ORGANS, width=120)
src = re.sub(r"ORGANS = \[.*?\n\]\n\n\ndef schema_for", organs_repr + "\n\n\ndef schema_for", src, count=1, flags=re.S)
(ROOT / "tools/governance/_alt19_ssp_bootstrap.py").write_text(src, encoding="utf-8")
print("ok")
