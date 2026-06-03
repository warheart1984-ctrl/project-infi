#!/usr/bin/env python3

"""Run URG mission demos: explicit organs + auto-assign (+ optional live organ)."""



from __future__ import annotations



import argparse

import json

import os

import sys

from pathlib import Path





def _run_demo(repo: Path, demo_path: Path, label: str, *, expect_steps: int = 3) -> int:

    if not demo_path.exists():

        print(f"error: missing {demo_path}")

        return 1



    mission = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    from src.ugr.mission.mission_runtime import UGRMissionRuntime



    result = UGRMissionRuntime().run_mission(mission)

    if result.get("status") != "ok":

        print(f"error: {label} status={result.get('status')}")

        return 1

    steps = result.get("steps") or []

    if len(steps) != expect_steps:

        print(f"error: {label} expected {expect_steps} steps")

        return 1

    if expect_steps == 3:

        providers = {s.get("provider") for s in steps}

        if providers != {"local", "openai", "openrouter"}:

            print(f"error: {label} unexpected providers {providers}")

            return 1

    receipt = result.get("mission_receipt") or {}

    if not receipt.get("content_digest"):

        print(f"error: {label} missing content_digest")

        return 1

    schema = result.get("mission_receipt_schema") or {}

    if not schema.get("receipt_sig") or not schema.get("ledger_root"):

        print(f"error: {label} missing mission_receipt_schema fields")

        return 1

    if schema.get("outcome") != "completed":

        print(f"error: {label} outcome={schema.get('outcome')}")

        return 1

    if schema.get("failure_reason"):

        print(f"error: {label} unexpected failure_reason={schema.get('failure_reason')}")

        return 1

    if not schema.get("urg_version"):

        print(f"error: {label} missing urg_version")

        return 1

    if not schema.get("cloud_identity_hash") or not schema.get("boundary_digest"):

        print(f"error: {label} missing cloud manifold proof fields")

        return 1

    if result.get("switchboard", {}).get("aais_step_bridge"):

        for step in steps:

            if not (step.get("aais_deliberation") or {}).get("bridge"):

                print(f"error: {label} step missing real bridge")

                return 1

    print(f"ugr mission demo {label}: PASS")

    return 0





def _run_live(repo: Path) -> int:

    if os.getenv("UGR_LLM_EXECUTE", "").strip().lower() not in {"1", "true", "yes", "on"}:

        print("ugr mission demo live: SKIP (set UGR_LLM_EXECUTE=1)")

        return 0

    demo_path = repo / "deploy" / "ugr" / "mission-demo-live.json"

    if not demo_path.exists():

        print("error: missing mission-demo-live.json")

        return 1

    mission = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    from src.ugr.mission.mission_runtime import UGRMissionRuntime



    result = UGRMissionRuntime().run_mission(mission)

    if result.get("status") != "ok":

        print(f"error: live status={result.get('status')} summary={result.get('summary')}")

        return 1

    schema = result.get("mission_receipt_schema") or {}

    if schema.get("outcome") != "completed":

        print(f"error: live outcome={schema.get('outcome')}")

        return 1

    if not schema.get("cloud_identity_hash") or not schema.get("boundary_digest"):

        print("error: live missing cloud proof fields")

        return 1

    steps = result.get("steps") or []

    if not steps:

        print("error: live no steps")

        return 1

    from src.ugr.mission.mission_ledger import MissionLedger



    rows = MissionLedger().list_for_mission(result["mission_id"])

    if not any(r.get("execution_committed") for r in rows):

        print("error: live ledger missing execution_committed")

        return 1

    print("ugr mission demo live: PASS")

    return 0





def _run_marketplace_admit(repo: Path) -> int:
    if os.getenv("URG_GOVERNANCE_APPLY", "").strip().lower() not in {"1", "true", "yes", "on"}:
        print("ugr marketplace admit: SKIP (set URG_GOVERNANCE_APPLY=1)")
        return 0
    os.environ.setdefault("URG_GOVERNANCE_OPERATOR_ALLOWLIST", "governance-operator")
    from src.ugr.mission.mission_runtime import UGRMissionRuntime

    payload = {
        "mission_kind": "governance_mutation",
        "mutation_target": "provider_organs",
        "mutation_op": "organ_admit",
        "operator_id": "governance-operator",
        "tenant_id": "tenant:acme",
        "organ_spec": {
            "organ_id": "organ-proof-admit",
            "tenant_scope": "tenant:acme",
            "status": "admitted",
            "identity": {"organ_id": "organ-proof-admit", "tier": "tiny", "label": "Proof Admit"},
            "envelope": {"proposal_only": True, "execution_backend": "local"},
            "function": {"capabilities": ["governed_super_router_demo"]},
            "contract": {
                "provider": "local",
                "max_cost_units": 1,
                "allowed_regions": ["tenant-us"],
                "allowed_domains": ["governed_super_router_demo"],
                "admissible_rails": ["SAFE"],
            },
        },
        "steps": [{"step_id": "gov", "objective": "admit"}],
    }
    result = UGRMissionRuntime().run_mission(payload)
    if result.get("status") != "ok":
        print(f"error: marketplace admit status={result.get('status')}")
        return 1
    print("ugr marketplace organ_admit: PASS")
    return 0


def _run_healthcheck(repo: Path) -> int:

    if os.getenv("UGR_LLM_EXECUTE", "").strip().lower() not in {"1", "true", "yes", "on"}:

        print("ugr mission healthcheck: SKIP (set UGR_LLM_EXECUTE=1)")

        return 0

    demo_path = repo / "deploy" / "ugr" / "mission-demo-healthcheck-embedding.json"

    if not demo_path.exists():

        print("error: missing mission-demo-healthcheck-embedding.json")

        return 1

    mission = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    mission["execution_mode"] = os.getenv("URG_EXECUTION_MODE", "LIVE_EXECUTION").strip().upper()

    from src.ugr.mission.mission_runtime import UGRMissionRuntime



    result = UGRMissionRuntime().run_mission(mission)

    if result.get("status") != "ok":

        print(f"error: healthcheck status={result.get('status')} summary={result.get('summary')}")

        return 1

    schema = result.get("mission_receipt_schema") or {}

    if schema.get("outcome") != "completed" or schema.get("failure_reason"):

        print(f"error: healthcheck receipt outcome={schema.get('outcome')} failure={schema.get('failure_reason')}")

        return 1

    if not schema.get("cloud_identity_hash") or not schema.get("boundary_digest") or not schema.get("receipt_sig"):

        print("error: healthcheck missing cryptographic proof fields")

        return 1

    from src.ugr.mission.mission_ledger import MissionLedger
    from src.ugr.platform.tenant_registry import normalize_tenant_id

    tenant_norm = normalize_tenant_id(mission.get("tenant_id") or "tenant-us")
    rows = MissionLedger(tenant_id=tenant_norm).list_for_mission(result["mission_id"])

    phases = [r.get("phase") for r in rows if r.get("type") == "urg_mission_transition"]

    for phase in ("mission_ingress", "organ_assignment", "provider_dispatch", "provider_ack"):

        if phase not in phases:

            print(f"error: healthcheck ledger missing phase {phase}")

            return 1

    step = (result.get("steps") or [{}])[0]

    if not step.get("execution_committed"):

        print("error: healthcheck step not execution_committed")

        return 1

    print("ugr mission healthcheck-embedding: PASS")

    return 0





def _run_federation_v17(repo: Path) -> int:
    from src.ugr.mission.federation_grants import CAP_ROUTE_STEP, FederationGrantStore
    from src.ugr.mission.mission_runtime import UGRMissionRuntime

    demo_path = repo / "deploy" / "ugr" / "mission-demo-federation-v17.json"
    if not demo_path.exists():
        print(f"error: missing {demo_path}")
        return 1
    mission = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]
    store = FederationGrantStore()
    grant = store.issue(
        issuer_tenant="tenant:acme",
        grantee_tenant="tenant:contoso",
        capabilities=[CAP_ROUTE_STEP],
        operator_id=str(mission.get("operator_id") or "operator-federation-demo"),
    )
    store.accept(
        grant.grant_id,
        accepting_tenant="tenant:contoso",
        operator_id="operator-contoso",
    )
    for step in mission.get("steps") or []:
        if step.get("federation_grant_id") == "__GRANT_ID__":
            step["federation_grant_id"] = grant.grant_id
    result = UGRMissionRuntime().run_mission(mission)
    if result.get("status") != "ok":
        print(f"error: federation-v17 status={result.get('status')} {result.get('summary')}")
        return 1
    print("ugr mission federation-v17: PASS")
    return 0


def main() -> int:

    parser = argparse.ArgumentParser(description="URG mission proof demos")

    parser.add_argument("--live", action="store_true", help="Run live provider organ demo (requires UGR_LLM_EXECUTE=1)")

    parser.add_argument(

        "--healthcheck",

        action="store_true",

        help="Run healthcheck-embedding governed mission (requires UGR_LLM_EXECUTE=1)",

    )

    parser.add_argument(

        "--marketplace-admit",

        action="store_true",

        help="Run governance organ_admit demo (requires URG_GOVERNANCE_APPLY=1 and allowlist)",

    )

    parser.add_argument(

        "--federation-v17",

        action="store_true",

        help="Run bilateral federation demo (issue grant, accept, federated step dual ledger)",

    )

    args = parser.parse_args()



    repo = Path(__file__).resolve().parents[2]

    sys.path.insert(0, str(repo))



    if args.live:

        return _run_live(repo)

    if args.healthcheck:

        return _run_healthcheck(repo)

    if getattr(args, "marketplace_admit", False):

        return _run_marketplace_admit(repo)

    if getattr(args, "federation_v17", False):

        return _run_federation_v17(repo)



    code = _run_demo(repo, repo / "deploy" / "ugr" / "mission-demo.json", "explicit")

    if code != 0:

        return code

    return _run_demo(repo, repo / "deploy" / "ugr" / "mission-demo-auto.json", "auto-assign")





if __name__ == "__main__":

    sys.exit(main())

