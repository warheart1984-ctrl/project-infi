#!/usr/bin/env python3
"""Read-only Platform Membrane governance gate."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REQUIRED = [
    "docs/subsystems/platform/PLATFORM_BLUEPRINT.md",
    "docs/subsystems/platform/PLATFORM_API_CONTRACT.md",
    "docs/subsystems/platform/ONBOARDING.md",
    "docs/runtime/PLATFORM_MEMBRANE.md",
    "platform/schemas/platform_job.v1.json",
    "platform/schemas/platform_artifact_ref.v1.json",
    "platform/schemas/platform_identity.v1.json",
    "platform/schemas/platform_role_binding.v1.json",
    "platform/api.py",
    "platform/store.py",
    "platform/extra_routes.py",
    "platform/jobs/graph.py",
    "platform/policy/engine.py",
    "docs/proof/platform/PLATFORM_V1_PROOF_BUNDLE.md",
    "docs/proof/platform/PLATFORM_V1_1_PROOF_BUNDLE.md",
]

FORBIDDEN_IMPORTS = (
    "from src.api",
    "import src.api",
    "from jarvis",
)


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (REPO / rel).is_file():
            errors.append(f"missing:{rel}")

    platform_py = REPO / "platform"
    if platform_py.is_dir():
        for path in platform_py.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            for needle in FORBIDDEN_IMPORTS:
                if needle in text:
                    errors.append(f"cognition_import:{path.relative_to(REPO)}:{needle}")

    if errors:
        print("platform-gate: FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("platform-gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
