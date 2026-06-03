#!/usr/bin/env python3
"""Alt-7 governed promotion eligibility — coherence fabric + Alt-6 dependency."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.operator_cognition_coherence_fabric import build_coherence_fabric_status
from tools.governance.check_alt6_governed_eligibility import check_eligibility as check_alt6_eligibility

GENE = "operator_cognition_coherence_fabric"
GOVERNED_PROOF = _ROOT / "docs/proof/platform/OPERATOR_COGNITION_COHERENCE_FABRIC_GOVERNED_PROOF.md"
BRIDGE_TESTS = _ROOT / "tests/test_coherence_fabric_bridge.py"


def _path_label(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _coherence_invariants_maturity(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for entry in (data.get("governance") or {}).get("invariants") or []:
        if isinstance(entry, str):
            errors.append(f"{GENE} invariants must be maturity-tagged objects")
            break
        if isinstance(entry, dict) and not entry.get("maturity"):
            errors.append(f"{GENE} invariant missing maturity")
    return errors


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = list(check_alt6_eligibility(root))

    from src.governance_organs.genome_engine import GenomeEngine

    GenomeEngine.reload(root)
    organ = GenomeEngine.registry().genomes.get(GENE)
    if not organ:
        errors.append(f"missing genome: {GENE}")
        return errors

    errors.extend(_coherence_invariants_maturity(organ))

    if not GOVERNED_PROOF.is_file():
        errors.append(f"missing governed proof bundle: {_path_label(GOVERNED_PROOF, root)}")

    status = build_coherence_fabric_status(root=root)
    if not status.get("fabric_genes_aligned"):
        errors.append("coherence fabric not aligned with Alt-6 fabric minimum")
    if not status.get("lane_awakened"):
        errors.append("adaptive lanes not awakened for coherence fabric")
    if str(status.get("authority_lane") or "") != "operator":
        errors.append(
            f"coherence authority_lane must be operator (got {status.get('authority_lane')!r})"
        )
    envelope_modes = status.get("envelope_governance_modes") or []
    if len(envelope_modes) != 4:
        errors.append(f"expected 4 envelope governance modes (got {len(envelope_modes)})")
    schema_version = str(status.get("operator_cognition_coherence_fabric_version") or "")
    if schema_version.endswith(".v1.1") or schema_version.endswith(".v1.2"):
        runtime_posture = status.get("runtime_posture") or []
        if len(runtime_posture) != 2:
            errors.append(
                f"expected 2 runtime_posture entries for {schema_version} (got {len(runtime_posture)})"
            )
    if schema_version.endswith(".v1.2"):
        if "coherence_pipeline_allowed" not in status:
            errors.append("coherence_pipeline_allowed missing from v1.2 snapshot")
        if "safety_envelope_halt" not in status:
            errors.append("safety_envelope_halt missing from v1.2 snapshot")

    if BRIDGE_TESTS.is_file():
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(BRIDGE_TESTS), "-q"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stdout or proc.stderr or "").strip().splitlines()
            suffix = detail[-1] if detail else "bridge coherence tests failed"
            errors.append(suffix)
    else:
        errors.append(f"missing bridge coherence tests: {_path_label(BRIDGE_TESTS, root)}")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt7-governed-gate] FAIL: {err}")
        return 1
    print("[alt7-governed-gate] PASS: coherence fabric eligible for governed promotion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
