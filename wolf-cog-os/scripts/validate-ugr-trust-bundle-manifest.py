#!/usr/bin/env python3
"""Validate UGR trust bundle organ artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_FILES = [
    "src/ugr/trust_bundle/organ.py",
    "src/ugr/trust_bundle/scenarios.py",
    "src/ugr/trust_bundle/evidence.py",
    "tools/proof/run_ugr_trust_bundle.py",
    "docs/contracts/UGR_TRUST_BUNDLE_ORGAN_CONTRACT.md",
    "docs/proof/ugr/UGR_TRUST_BUNDLE_ORGAN_PROOF.md",
    "docs/trust_bundles/2026-05-28-ugr-trust-bundle-organ.md",
    "tests/test_ugr_trust_bundle_organ.py",
]


def validate_trust_bundle_record(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"missing trust bundle record: {path}"]
    text = path.read_text(encoding="utf-8")
    if "claim_label:" not in text:
        findings.append(f"{path}: missing claim_label block")
    if "proof_links:" not in text:
        findings.append(f"{path}: missing proof_links block")
    if "override_command:" not in text:
        findings.append(f"{path}: missing override_command")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UGR trust bundle organ manifest.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append(f"missing required file: {rel}")
    findings.extend(validate_trust_bundle_record(root / "docs/trust_bundles/2026-05-28-ugr-trust-bundle-organ.md"))
    status = "pass" if not findings else "fail"
    print(f"ugr trust bundle manifest validation: status={status}, findings={len(findings)}")
    for item in findings:
        print(f"  - {item}")
    if findings and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
