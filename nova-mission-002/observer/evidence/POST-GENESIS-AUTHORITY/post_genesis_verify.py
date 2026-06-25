#!/usr/bin/env python3
"""Verify PGA-PKG-1 post-genesis authority evidence pack (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(data: Any) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def replay_steward_state(
    genesis: dict[str, Any],
    events: list[dict[str, Any]],
    r0: dict[str, Any],
) -> dict[str, Any]:
    stewards = {s["steward_id"]: dict(s) for s in genesis["stewards"]}
    quorum = genesis["quorum_threshold"]
    stalled = False

    for event in events:
        etype = event["event_type"]
        sigs = event.get("quorum_signatures", [])
        min_sigs = r0["quorum_rules"].get(etype.replace("steward_", "steward_"), {}).get(
            "min_signatures", quorum
        )
        if etype == "steward_key_rotation":
            min_sigs = r0["quorum_rules"]["key_rotation"]["min_signatures"]
        elif etype == "steward_added":
            min_sigs = r0["quorum_rules"]["steward_add"]["min_signatures"]
        elif etype == "steward_removed":
            min_sigs = r0["quorum_rules"]["steward_remove"]["min_signatures"]
        elif etype == "quorum_dispute":
            if event.get("outcome") == "system_stall":
                stalled = True
            continue

        if len(sigs) < min_sigs:
            raise ValueError(f"quorum not met for {event['event_id']}")

        if etype == "steward_key_rotation":
            sid = event["steward_id"]
            if sid not in stewards or stewards[sid]["status"] != "active":
                raise ValueError(f"invalid rotation target {sid}")
            stewards[sid]["key"] = event["new_key"]
        elif etype == "steward_added":
            sid = event["steward_id"]
            stewards[sid] = {
                "steward_id": sid,
                "display_name": sid,
                "key": event["key"],
                "status": "active",
            }
        elif etype == "steward_removed":
            sid = event["steward_id"]
            if sid not in stewards:
                raise ValueError(f"unknown steward {sid}")
            stewards[sid]["status"] = "removed"

    active = sorted(
        sid for sid, s in stewards.items() if s.get("status") == "active"
    )
    return {
        "active_stewards": active,
        "steward_count": len(active),
        "stalled": stalled,
        "keys": {sid: stewards[sid]["key"] for sid in active},
    }


def verify_package(bundle_dir: Path, package_path: Path) -> dict[str, Any]:
    package = load_json(package_path)
    artifacts_dir = bundle_dir / "artifacts"
    receipts_dir = bundle_dir / "receipts"

    checks: dict[str, bool] = {}

    r0_path = artifacts_dir / "R0.root.json"
    s0_path = artifacts_dir / "S0.genesis.json"
    log_path = artifacts_dir / "S0.event_log.jsonl"
    clg_path = artifacts_dir / "CLG-1.snapshot.json"

    artifact_hashes = {
        "R0": sha256_file(r0_path),
        "S0_genesis": sha256_file(s0_path),
        "S0_event_log": sha256_file(log_path),
        "CLG1": sha256_file(clg_path),
    }
    checks["artifact_hashes"] = artifact_hashes == package["artifact_hashes"]

    r0 = load_json(r0_path)
    checks["r0_immutable"] = (
        r0["mutation_policy"]["runtime_mutable"] is False
        and r0["mutation_policy"]["amendment_channel_access"] is False
        and r0["mutation_policy"]["ce1_correction_access"] is False
    )

    events = load_events(log_path)
    genesis = load_json(s0_path)
    final_state = replay_steward_state(genesis, events, r0)
    checks["final_state_hash"] = (
        sha256_json(final_state) == package["expected_final_state_hash"]
    )
    checks["constitutional_stall"] = final_state["stalled"] is True

    clg = load_json(clg_path)
    clg_nodes = {n["node_id"]: n for n in clg["nodes"]}
    for event in events:
        node = clg_nodes.get(event["clg_node"])
        checks.setdefault("lineage_anchored", True)
        if not node or node["event_ref"] != event["event_id"]:
            checks["lineage_anchored"] = False

    for receipt_ref in package["receipt_refs"]:
        receipt = load_json(receipts_dir / receipt_ref["file"])
        checks[f"receipt_{receipt['receipt_id']}"] = (
            receipt["governance_event_id"]
            == next(e["event_id"] for e in events if e["grr_receipt_id"] == receipt["receipt_id"])
        )

    recomputed = sha256_json(
        {
            "artifact_hashes": package["artifact_hashes"],
            "expected_final_state_hash": package["expected_final_state_hash"],
            "mission_id": package["mission_id"],
            "receipt_refs": package["receipt_refs"],
        }
    )
    checks["canonical_hash"] = recomputed == package["canonical_hash"]

    status = "verified" if all(checks.values()) else "failed"
    return {
        "status": status,
        "canonical_hash": package["canonical_hash"],
        "checks": checks,
        "final_state": final_state,
        "recomputed_hash": recomputed,
    }


def build_package(bundle_dir: Path) -> dict[str, Any]:
    artifacts_dir = bundle_dir / "artifacts"
    r0 = load_json(artifacts_dir / "R0.root.json")
    genesis = load_json(artifacts_dir / "S0.genesis.json")
    events = load_events(artifacts_dir / "S0.event_log.jsonl")
    final_state = replay_steward_state(genesis, events, r0)

    artifact_hashes = {
        "R0": sha256_file(artifacts_dir / "R0.root.json"),
        "S0_genesis": sha256_file(artifacts_dir / "S0.genesis.json"),
        "S0_event_log": sha256_file(artifacts_dir / "S0.event_log.jsonl"),
        "CLG1": sha256_file(artifacts_dir / "CLG-1.snapshot.json"),
    }

    receipt_refs = [
        {"file": "grr-001-key-rotation.json", "receipt_id": "grr-001-key-rotation"},
        {"file": "grr-002-steward-added.json", "receipt_id": "grr-002-steward-added"},
        {"file": "grr-003-steward-removed.json", "receipt_id": "grr-003-steward-removed"},
        {"file": "grr-004-quorum-dispute.json", "receipt_id": "grr-004-quorum-dispute"},
    ]

    expected_final_state_hash = sha256_json(final_state)
    mission_id = "MISSION-GOV-POST-GENESIS-AUTHORITY-v1.0"

    canonical_hash = sha256_json(
        {
            "artifact_hashes": artifact_hashes,
            "expected_final_state_hash": expected_final_state_hash,
            "mission_id": mission_id,
            "receipt_refs": receipt_refs,
        }
    )

    return {
        "id": "PGA-PKG-1",
        "designation": "CP-GOV-001",
        "version": "1.0",
        "mission_id": mission_id,
        "artifact_hashes": artifact_hashes,
        "receipt_refs": receipt_refs,
        "lineage_anchors": [
            {"node": "CLG-1:node:00017", "maps_to": "steward_key_rotation:steward:03"},
            {"node": "CLG-1:node:00023", "maps_to": "steward_added:steward:05"},
            {"node": "CLG-1:node:00029", "maps_to": "steward_removed:steward:02"},
            {"node": "CLG-1:node:00031", "maps_to": "quorum_dispute:qd:0004"},
        ],
        "expected_final_state": final_state,
        "expected_final_state_hash": expected_final_state_hash,
        "canonical_hash": canonical_hash,
        "verdict": "PASS",
    }


def main() -> int:
    bundle_dir = Path(__file__).resolve().parent
    package_path = bundle_dir / "PGA-PKG-1.json"

    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        package = build_package(bundle_dir)
        package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
        print(f"built {package_path.name}")
        print(f"canonical_hash: {package['canonical_hash']}")
        return 0

    if not package_path.exists():
        build_package(bundle_dir)
        package_path.write_text(
            json.dumps(build_package(bundle_dir), indent=2) + "\n",
            encoding="utf-8",
        )

    result = verify_package(bundle_dir, package_path)
    print(f"status: {result['status']}")
    print(f"canonical_hash: {result['canonical_hash']}")
    if result["status"] != "verified":
        for name, ok in result["checks"].items():
            if not ok:
                print(f"FAIL: {name}", file=sys.stderr)
        return 1
    print(f"active_stewards: {result['final_state']['active_stewards']}")
    print(f"constitutional_stall: {result['final_state']['stalled']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
