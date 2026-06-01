#!/usr/bin/env python3
"""Validate cross-build lineage reproducibility (P12)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_LIB_DIR = _SCRIPT_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from forge_lineage import compute_lineage_id  # noqa: E402


REPRO_FIELDS = (
    "schema_version",
    "pipeline_name",
    "variant_id",
    "profile_id",
    "substrate_id",
    "rootfs_backend",
    "replay_adapter",
    "package_sets",
    "target_arch",
    "reproducibility_seed",
    "parent_lineage_id",
    "cogos_tag",
    "pipeline_path",
    "git_commit",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge lineage reproducibility.")
    parser.add_argument("--lineage-a", required=True, help="First lineage artifact path.")
    parser.add_argument("--lineage-b", default="", help="Optional second lineage artifact for comparison.")
    parser.add_argument("--ignore-build-host", action="store_true", help="Exclude build_host from comparison.")
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def load_lineage(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def repro_snapshot(payload: dict, *, ignore_build_host: bool) -> dict:
    snap = {key: payload.get(key) for key in REPRO_FIELDS}
    if ignore_build_host:
        snap.pop("build_host", None)
    return snap


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    path_a = repo_root / args.lineage_a
    findings: list[str] = []

    if not path_a.is_file():
        findings.append(f"lineage-a missing: {path_a}")
    else:
        payload_a = load_lineage(path_a)
        recomputed = compute_lineage_id(payload_a)
        observed = str(payload_a.get("lineage_id", ""))
        if observed != recomputed:
            findings.append("lineage-a lineage_id does not match recomputed hash")

    if args.lineage_b:
        path_b = repo_root / args.lineage_b
        if not path_b.is_file():
            findings.append(f"lineage-b missing: {path_b}")
        elif path_a.is_file():
            payload_b = load_lineage(path_b)
            recomputed_b = compute_lineage_id(payload_b)
            if str(payload_b.get("lineage_id", "")) != recomputed_b:
                findings.append("lineage-b lineage_id does not match recomputed hash")
            snap_a = repro_snapshot(payload_a, ignore_build_host=args.ignore_build_host)
            snap_b = repro_snapshot(payload_b, ignore_build_host=args.ignore_build_host)
            if snap_a != snap_b:
                findings.append("reproducibility component mismatch between lineage-a and lineage-b")
            elif payload_a.get("lineage_id") != payload_b.get("lineage_id"):
                findings.append("lineage_id mismatch for identical reproducibility components")

    status = "pass" if not findings else "fail"
    result = {
        "validator": "forge-lineage-reproducibility.v1",
        "status": status if args.mode == "fail" or status == "pass" else "warn",
        "lineage_a": str(path_a),
        "lineage_b": str(repo_root / args.lineage_b) if args.lineage_b else "",
        "findings": findings,
    }
    if args.output:
        out = repo_root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"lineage reproducibility: status={result['status']} findings={len(findings)}")
    for finding in findings:
        print(f"[ERROR] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
