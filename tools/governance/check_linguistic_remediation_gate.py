#!/usr/bin/env python3
"""Verify remediation playbooks exist for high-drift genes."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_remediation_engine import playbook_exists  # noqa: E402
from tools.linguistic_genome_lib import load_json  # noqa: E402


def main() -> int:
    root = _ROOT
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    mode = "observe"
    if reg_path.is_file():
        mode = load_json(reg_path).get("policy_mode", "observe")

    drift_path = root / "governance/linguistic_drift_report.v1.json"
    if not drift_path.is_file():
        print("linguistic-remediation-gate: SKIP (no drift report; run linguistic-drift-gate)")
        return 0

    data = load_json(drift_path)
    errors: list[str] = []
    warnings: list[str] = []
    high_genes = [e["gene"] for e in data.get("scores", []) if e.get("band") == "high"]

    for gene in high_genes:
        if not playbook_exists(gene, root):
            msg = f"{gene}: missing remediation playbook"
            if mode == "enforce":
                errors.append(msg)
            else:
                warnings.append(msg)

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"linguistic-remediation-gate: FAIL ({len(errors)} error(s))")
        return 1
    print(
        f"linguistic-remediation-gate: PASS ({len(high_genes)} high-drift gene(s), "
        f"{len(warnings)} warning(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
