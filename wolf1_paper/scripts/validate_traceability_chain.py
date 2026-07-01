#!/usr/bin/env python3
"""Validate complete Requirement → ADR → Implementation → CTS → Evidence chains."""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import yaml
except ImportError:
    print("[TRACEABILITY] PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_yaml(path: pathlib.Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def main() -> int:
    reqs = load_yaml(ROOT / "registries" / "requirements.yaml")
    adrs = load_yaml(ROOT / "registries" / "adrs.yaml")
    impl = load_yaml(ROOT / "registries" / "implementations.yaml")
    cts = load_yaml(ROOT / "registries" / "cts.yaml")
    ev = load_yaml(ROOT / "registries" / "evidence.yaml")
    bench = load_yaml(ROOT / "registries" / "benchmarks.yaml")

    adrs_by_req = {a["requirement_id"]: a for a in adrs.get("adrs", [])}
    impl_by_req = {i["requirement_id"]: i for i in impl.get("implementations", [])}
    cts_by_req = {c["requirement_id"]: c for c in cts.get("cases", [])}
    ev_by_req = {e["requirement_id"]: e for e in ev.get("entries", [])}
    bench_by_req = {b["requirement_id"]: b for b in bench.get("benchmarks", [])}

    failures = []

    for req in reqs.get("requirements", []):
        rid = req["id"]
        missing = []
        if rid not in adrs_by_req:
            missing.append("ADR")
        if rid not in impl_by_req:
            missing.append("ReferenceImplementation")
        if rid not in cts_by_req:
            missing.append("CTS")
        if rid not in ev_by_req:
            missing.append("EvidenceLedger")
        if req.get("benchmark_required", False) and rid not in bench_by_req:
            missing.append("Benchmark")

        if missing:
            failures.append({"requirement_id": rid, "missing": missing})

    if failures:
        print("[TRACEABILITY] Incomplete requirements:")
        print(json.dumps(failures, indent=2))
        return 1

    print("[TRACEABILITY] All normative requirements have complete chains.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
