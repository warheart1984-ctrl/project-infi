# Cloud Forge Phase 1 Proof Packet

Claim: Rail scheduler library (`choose_rail`, `build_plan`, `schedule_request`) satisfies `aais.cloud_forge.rail.v1` adversarial rules.

Claim status: **proven** (Python 3.12 unit test run, 20 tests, exit 0).

Authority: `docs/contracts/cloud-forge-rail-contract.md`, `REPO_PROOF_LAW.md`.

## Scope

| ID | Deliverable | Path |
|---|---|---|
| C1-1 | Types | `src/cloud_forge/types.py` |
| C1-2 | Risk estimation | `src/cloud_forge/risk.py` |
| C1-3 | Rail selection + plan | `src/cloud_forge/rails.py` |
| C1-4 | Failsafe probe | `src/cloud_forge/failsafe.py` |
| C1-5 | Unit tests | `tests/test_cloud_forge_rails.py` |
| C1-6 | Pipeline hook | `src/governed_direct_pipeline.py` (`cloud_forge_context`) |
| C1-7 | UGR deliberation hook | `src/ugr/cloud_forge_bridge.py`, `src/ugr/unified_runtime.py` |
| C1-8 | UGR bridge tests | `tests/test_ugr_cloud_forge_bridge.py` |

## Verification command

```bash
py -3.12 -m unittest tests.test_cloud_forge_rails -v
py -3.12 -m pytest tests/test_ugr_cloud_forge_bridge.py -q
```

## Evidence (2026-05-28)

```
Ran 20 tests in 3.563s

OK
```

Environment: `E:/project-infi`, Python 3.12, Windows.

Adversarial cases covered:

- `mutation_scope: constitutional` → SAFE
- `required_proof: true` → SAFE
- `CLOUD_FORGE_FORCE_SAFE=1` → SAFE
- `immune_elevated` → SAFE
- MEDIUM write → never EXPRESS
- `forbid_express` → NORMAL cap
- Law cache cap `forbid_cache_above: L0` on EXPRESS plan
- Pipeline `cloud_forge_context` attaches bundle
- UGR `/api/ugr/deliberate` attaches `rail_decision` + trace summary

## UGR hook evidence (2026-05-28)

Command:

```bash
py -3.12 -m pytest tests/test_ugr_cloud_forge_bridge.py -q
```

Result: **9 passed** (Python 3.12, Windows, `E:/project-infi`).

UGR trace fields: `rail`, `risk`, `law_ceiling`, `rationale_codes`, `cache_mode`, `model_tier`.
Disable hook: `UGR_CLOUD_FORGE_ENABLED=0`. Observed ledger path: `UGR_CLOUD_FORGE_OBSERVED=1`.

## Why

Phase 1 implements the contract selection algorithm as pure functions with inspectable `RailDecision` and `CognitionPlan` outputs before caches or cloud locality (Phase 3–4).

## Explicit non-claims

- No cross-machine p95 latency benchmarks (CF-D5 open).
- No Pattern Ledger JSONL writer (Phase 2).
- Default `python` 3.10 on host may fail unrelated `src` imports; use 3.12+ for verification.

## Next gate

Phase 2: ledger adapter + EXPRESS domain template `forge/voss/os_architecture`.
