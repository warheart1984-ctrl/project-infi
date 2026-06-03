#!/usr/bin/env python3
"""Release 27.2 CISIV Early Ideas Bundle closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/CISIV_EARLY_IDEAS_BUNDLE_V1_PROOF.md",
)
ALT27_GENES = (
    "cisiv_operator_lineage_console",
    "forensic_triangulation",
    "capability_service_bridge",
    "jarvis_memory_board",
    "governed_direct_pipeline",
    "recipe_module",
    "imagine_generator",
    "narrative_trust_pack",
    "human_voice_extraction",
)
ORGAN_TESTS = (
    "tests/test_ul_lineage_console_organ.py",
    "tests/test_forensic_triangulation_organ.py",
    "tests/test_recipe_module_organ.py",
    "tests/test_imagine_generator_organ.py",
    "tests/test_narrative_trust_pack_organ.py",
    "tests/test_human_voice_extraction_organ.py",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt27-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    tests = list(ORGAN_TESTS) + [
        "tests/test_operator_cognition_coherence_fabric.py::test_alt27_early_ideas_layers_at_v122"
    ]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *tests, "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return 1
    schema = _ROOT / "schemas/operator_cognition_coherence_fabric.v1.22.json"
    if not schema.is_file():
        print("[alt27-closure-gate] FAIL: missing coherence v1.22 schema")
        return 1
    print("[alt27-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
