#!/usr/bin/env python3
"""Emit a local or CI promotion dry-run readiness report."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit promotion dry-run readiness report.")
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--expected-profile-id", default="")
    parser.add_argument("--required-scenarios", default="1,3,4,6")
    parser.add_argument("--promotion-validation", default="")
    parser.add_argument("--output", default="ci-artifacts/promotion-dry-run-report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts_dir = Path(args.artifacts_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    required_files = [
        "build-metadata.json",
        "matrix-summary.json",
        "artifact-manifest.json",
        "state.json",
    ]
    forge_files = [
        "profile-attestation.json",
        "profile-validation.json",
        "profile-resolution.json",
        "forge-build-state.json",
        "forge-lineage.json",
    ]

    missing = [name for name in required_files if not (artifacts_dir / name).is_file()]
    missing_forge: list[str] = []
    if args.expected_profile_id:
        missing_forge = [name for name in forge_files if not (artifacts_dir / name).is_file()]

    iso_files = sorted(artifacts_dir.glob("*.iso"))
    sig_files = sorted(artifacts_dir.glob("*.minisig"))

    promotion_validation = {}
    validation_path = Path(args.promotion_validation) if args.promotion_validation else artifacts_dir / "promotion-source-validation.json"
    if validation_path.is_file():
        promotion_validation = json.loads(validation_path.read_text(encoding="utf-8"))

    status = "pass"
    notes: list[str] = []
    if missing:
        status = "fail"
        notes.append("missing required artifacts: " + ",".join(missing))
    if missing_forge:
        status = "fail"
        notes.append("missing forge promotion artifacts: " + ",".join(missing_forge))
    if not iso_files:
        status = "fail"
        notes.append("missing promotable ISO")
    if promotion_validation.get("status") == "fail":
        status = "fail"
        notes.append("promotion-source validation failed")

    report = {
        "schema_version": "promotion-dry-run.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "dry_run": True,
        "source_run_id": args.source_run_id,
        "expected_profile_id": args.expected_profile_id,
        "required_scenarios": args.required_scenarios,
        "artifact_inventory": {
            "iso_count": len(iso_files),
            "signature_count": len(sig_files),
            "missing_required": missing,
            "missing_forge": missing_forge,
        },
        "promotion_source_validation": promotion_validation,
        "notes": notes,
    }

    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"promotion dry-run report: status={status} output={output_path}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
