# URG Mission Quickstart

**AAIS** = governed cognitive runtime (per-turn).  
**URG** = unified runtime governance — lawbook + switchboard for models (not a model).

## Run the brutal demo

One mission, three provider organs, cost + risk + region constraints, fully ledgered (v1.2: real AAIS bridge per step).

```bash
cd project-infi
py -3.12 tools/proof/run_ugr_mission_demo.py
```

Auto-assign (no `organ_id`, use `tier` on each step):

```bash
py -3.12 -c "import json; from src.ugr.mission.mission_runtime import UGRMissionRuntime; m=json.load(open('deploy/ugr/mission-demo-auto.json'))['mission']; print(UGRMissionRuntime().run_mission(m)['status'])"
```

HMAC receipt key (optional):

```bash
set URG_OPERATOR_RECEIPT_KEY=your-operator-secret
```

Or via API (Jarvis Flask on your AAIS port):

```bash
curl -s -X POST http://127.0.0.1:5000/api/ugr/mission/run \
  -H "Content-Type: application/json" \
  -d @deploy/ugr/mission-demo.json
```

Use the `mission` object inside the JSON file as the POST body if your client does not unwrap automatically.

## Gate

```bash
make ugr-mission-gate
```

## Contracts

- Stack naming: [URG_STACK_DOCTRINE.md](../contracts/URG_STACK_DOCTRINE.md)
- Mission API: [URG_MISSION_CONTRACT.md](../contracts/URG_MISSION_CONTRACT.md)
- Cloud invariants: [URG_CLOUD_INVARIANTS.md](../contracts/URG_CLOUD_INVARIANTS.md)
- Provider organs: [URG_PROVIDER_ORGAN_CONTRACT.md](../contracts/URG_PROVIDER_ORGAN_CONTRACT.md)
- Receipt signing: [URG_MISSION_RECEIPT_SIGNING.md](../contracts/URG_MISSION_RECEIPT_SIGNING.md)

## Ingress law

If it did not pass through URG (`urg_ingress` stamp on the mission), it does not exist. Product code must not call provider registries directly for governed cloud paths.

## Optional execution

Provider proposals stay proposal-only unless you explicitly enable governed execution (same law as the LLM lane):

```bash
set UGR_LLM_EXECUTE=1
```
