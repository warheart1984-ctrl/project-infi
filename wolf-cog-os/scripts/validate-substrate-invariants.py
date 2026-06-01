#!/usr/bin/env python3
"""Validate universal substrate governance invariants registry (P15)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Forge substrate invariants registry.")
    parser.add_argument(
        "--invariants",
        default="wolf-cog-os/forge/governance/substrate-invariants.json",
    )
    parser.add_argument(
        "--substrate-registry",
        default="wolf-cog-os/forge/substrates/registry.json",
    )
    parser.add_argument(
        "--replay-registry",
        default="wolf-cog-os/forge/replay-adapters/registry.json",
    )
    parser.add_argument(
        "--backend-registry",
        default="wolf-cog-os/forge/backends/registry.json",
    )
    parser.add_argument("--mode", choices=["warn", "fail"], default="fail")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    inv_path = repo_root / args.invariants
    if not inv_path.is_file():
        print(f"ERROR: invariants registry missing: {inv_path}", file=sys.stderr)
        return 2

    invariants = json.loads(inv_path.read_text(encoding="utf-8"))
    substrates = json.loads((repo_root / args.substrate_registry).read_text(encoding="utf-8")).get("substrates", {})
    replay = json.loads((repo_root / args.replay_registry).read_text(encoding="utf-8")).get("adapters", {})
    backends = json.loads((repo_root / args.backend_registry).read_text(encoding="utf-8")).get("backends", {})

    findings: list[str] = []
    for platform, spec in invariants.get("platforms", {}).items():
        adapter_id = str(spec.get("replay_adapter", ""))
        backend_id = str(spec.get("backend", ""))
        if adapter_id not in replay:
            findings.append(f"{platform}: replay adapter not registered: {adapter_id}")
        elif not replay[adapter_id].get("wired_in_build"):
            findings.append(f"{platform}: replay adapter not wired: {adapter_id}")
        if backend_id not in backends:
            findings.append(f"{platform}: backend not registered: {backend_id}")
        module = repo_root / f"wolf-cog-os/scripts/lib/replay-adapters/{adapter_id}.sh"
        if not module.is_file():
            findings.append(f"{platform}: replay module missing: {module.name}")
        backend_module = repo_root / f"wolf-cog-os/scripts/lib/backends/{backend_id}.sh"
        if not backend_module.is_file():
            findings.append(f"{platform}: backend module missing: {backend_module.name}")
        for substrate_id in spec.get("substrate_ids", []):
            if substrate_id not in substrates:
                findings.append(f"{platform}: substrate id missing from registry: {substrate_id}")
            elif substrates[substrate_id].get("replay_adapter") != adapter_id:
                findings.append(f"{platform}: substrate {substrate_id} adapter mismatch")

    status = "pass" if not findings else "fail"
    print(
        f"substrate invariants validation: status={status}, "
        f"platforms={len(invariants.get('platforms', {}))}, findings={len(findings)}"
    )
    for finding in findings:
        print(f"[ERROR] {finding}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
