#!/usr/bin/env python3
"""Governance gate for Platform Membrane v8–v14."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    required = [
        "platform/billing/engine.py",
        "platform/auth/oidc_providers.py",
        "platform/routing/region.py",
        "platform/drift/scheduler.py",
        "platform/assistant/query.py",
        "platform/policy/compile.py",
        "platform/workflow/engine.py",
        "platform/schemas/org_policy_dsl.v1.json",
        "platform/v814_routes.py",
        "docs/proof/platform/PLATFORM_V8_PROOF_BUNDLE.md",
        "frontend/src/pages/PlatformAssistant.jsx",
        "frontend/src/pages/PlatformWorkflow.jsx",
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            fail(f"missing {rel}")

    assistant = (ROOT / "platform/assistant/query.py").read_text(encoding="utf-8")
    for banned in ("from src.api", "from src import api", "JobRegistry", "create_job("):
        if banned in assistant:
            fail(f"MA-13 violation in assistant: {banned}")

    for mod in ROOT.glob("platform/assistant/**/*.py"):
        text = mod.read_text(encoding="utf-8")
        if "src.api" in text or "nova" in text.lower() and "platform" not in str(mod):
            if "nova" in text and "from nova" in text:
                fail(f"assistant imports cognition: {mod}")

    manifest = ROOT / "docs/proof/platform/cross_machine/REPLAY_MANIFEST.template.json"
    if '"operational_status": "inactive"' in manifest.read_text(encoding="utf-8"):
        fail("cross_machine replay manifest must be active for v12")

    print("OK: platform v8-v14 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
