#!/usr/bin/env python3

"""Validate URG mission-level governance artifacts."""



from __future__ import annotations



import argparse

import json

from pathlib import Path

import sys





REQUIRED_FILES = [

    "docs/contracts/URG_STACK_DOCTRINE.md",

    "docs/contracts/URG_CLOUD_INVARIANTS.md",

    "docs/contracts/URG_MISSION_CONTRACT.md",

    "docs/contracts/URG_PROVIDER_ORGAN_CONTRACT.md",

    "docs/contracts/URG_MISSION_RECEIPT_SIGNING.md",

    "docs/contracts/URG_MISSION_RECEIPT_SCHEMA.md",

    "schemas/urg_mission_receipt.v1.json",

    "deploy/ugr/provider-organs.json",

    "deploy/ugr/aais-instances.json",

    "deploy/ugr/mission-demo.json",

    "deploy/ugr/mission-demo-auto.json",

    "deploy/ugr/mission-demo-live.json",
    "deploy/ugr/mission-demo-healthcheck-embedding.json",
    "deploy/ugr/mission-demo-federation-v17.json",
    "deploy/ugr/tenants.json",
    "deploy/ugr/tenants/tenant-acme/provider-organs.json",
    "src/ugr/mission/execution_policy.py",
    "src/ugr/mission/step_execution.py",
    "src/ugr/mission/tenant_manifold.py",
    "src/ugr/mission/federation_grants.py",
    "src/ugr/mission/cost_routing.py",
    "src/ugr/mission/marketplace.py",
    "src/ugr/mission/organ_trust.py",
    "src/ugr/invariants/execution_safety.py",

    "src/ugr/mission/mission_runtime.py",

    "src/ugr/mission/provider_organ.py",

    "src/ugr/mission/cloud_invariants.py",

    "src/ugr/mission/ingress.py",

    "src/ugr/mission/composite_mission.py",

    "src/ugr/mission/aais_step_bridge.py",

    "src/ugr/mission/aais_instance_registry.py",

    "src/ugr/mission/organ_matcher.py",

    "src/ugr/mission/receipt_signing.py",

    "src/ugr/mission/mission_receipt.py",
    "src/ugr/mission/governance_mission.py",
    "src/ugr/invariants/cloud_manifold.py",
    "src/ugr/invariants/cloud_invariants.py",

    "src/ugr/mission/mission_receipt_store.py",

    "src/ugr/mission/ledger_merkle.py",

    "tools/proof/run_ugr_mission_demo.py",

]





def validate_provider_organs(path: Path) -> list[str]:

    findings: list[str] = []

    if not path.exists():

        return [f"missing provider organs: {path}"]

    payload = json.loads(path.read_text(encoding="utf-8"))

    organs = dict(payload.get("organs") or {})

    if len(organs) < 3:

        findings.append(f"{path}: expected at least 3 demo organs")

    for organ_id, spec in organs.items():

        contract = dict(spec.get("contract") or {})

        if not contract.get("provider"):

            findings.append(f"{path}: organ {organ_id} missing contract.provider")

        if not bool(dict(spec.get("envelope") or {}).get("proposal_only", False)):

            findings.append(f"{path}: organ {organ_id} must be proposal_only")

    return findings





def validate_mission_demo(path: Path) -> list[str]:

    findings: list[str] = []

    if not path.exists():

        return [f"missing mission demo: {path}"]

    payload = json.loads(path.read_text(encoding="utf-8"))

    mission = dict(payload.get("mission") or {})

    steps = list(mission.get("steps") or [])

    if path.name == "mission-demo.json" and len(steps) != 3:

        findings.append(f"{path}: demo requires exactly 3 steps")

    if path.name == "mission-demo-live.json" and len(steps) < 1:

        findings.append(f"{path}: live demo requires at least one step")

    return findings





def validate_aais_instances(path: Path) -> list[str]:

    findings: list[str] = []

    if not path.exists():

        return [f"missing aais instances: {path}"]

    payload = json.loads(path.read_text(encoding="utf-8"))

    instances = dict(payload.get("instances") or {})

    if "aais-primary" not in instances:

        findings.append(f"{path}: missing aais-primary instance")

    return findings





def main() -> int:

    parser = argparse.ArgumentParser(description="Validate URG mission manifest.")

    parser.add_argument("--repo-root", default=".")

    parser.add_argument("--mode", choices=("warn", "fail"), default="fail")

    args = parser.parse_args()

    root = Path(args.repo_root).resolve()

    findings: list[str] = []

    for rel in REQUIRED_FILES:

        if not (root / rel).exists():

            findings.append(f"missing required file: {rel}")

    findings.extend(validate_provider_organs(root / "deploy/ugr/provider-organs.json"))

    findings.extend(validate_mission_demo(root / "deploy/ugr/mission-demo.json"))

    findings.extend(validate_mission_demo(root / "deploy/ugr/mission-demo-live.json"))

    findings.extend(validate_aais_instances(root / "deploy/ugr/aais-instances.json"))

    status = "pass" if not findings else "fail"

    print(f"ugr mission manifest validation: status={status}, findings={len(findings)}")

    for item in findings:

        print(f"  - {item}")

    if findings and args.mode == "fail":

        return 1

    return 0





if __name__ == "__main__":

    sys.exit(main())

