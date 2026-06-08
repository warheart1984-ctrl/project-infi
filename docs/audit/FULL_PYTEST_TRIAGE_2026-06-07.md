# Full pytest triage — 2026-06-07

Artifact paths:
- Pre–safety-fix baseline (reference): prior run — **123 failed**, **1817 passed** (skip count not recorded in reference).
- Post–safety-fix baseline: `ci-artifacts/full_pytest_baseline_2026-06-07_post_safety_fix.txt`
- Post–bridge-action + genome-boot-fix baseline: `ci-artifacts/full_pytest_baseline_2026-06-07_post_bridge_action_fix.txt`

Run command (post fix):

```text
python -m pytest tests/ -q --tb=no
```

Duration (post safety fix): ~33m32s (2012.27s).
Duration (post bridge + genome boot): ~52m36s (3156.31s).

## Summary

| Run | Failed | Passed | Skipped | Δ failed vs 123 |
|-----|--------|--------|---------|-----------------|
| Prior baseline | 123 | 1817 | — | — |
| Post safety fix | **41** | **1903** | **8** | **−82** |
| Post cluster fix (coherence v1.24 + test_api) | **17** | **1927** | **8** | **−106** |
| Post bridge action + genome boot fix | **23** | **1977** | **8** | **−100** |

OTEM / substrate / safety envelope slice (quick gate):

```text
python -m pytest tests/test_substrate_evolution_ledger.py tests/test_universal_substrate.py tests/test_otem_execution_approval_bridge.py tests/test_subsystem_mvp_integration.py tests/test_safety_envelope_organ.py -q
```

**34 passed**, 0 failed (2026-06-07).

## Failure clusters (by test file, post safety fix)

| Cluster | Test file(s) | Failures | Notes |
|---------|----------------|----------|-------|
| Chat API / patch & workbench | `tests/test_api.py` | 11 | Patch review/apply, state hygiene, workbench scope |
| Operator cognition / ALT planes | `tests/test_operator_cognition_coherence_fabric.py` | 10 | ALT12–ALT27 plane/version alignment |
| Coherence fabric execution | `tests/test_coherence_fabric_bridge.py`, `tests/test_adaptive_lane_bridge.py`, `tests/test_coherence_fabric_pipeline.py` | 7 | Lane/fabric alignment, safety halt blocks |
| Forge ship/platform gates | `tests/test_forge_shippable_gate.py`, `tests/test_forge_platform_gate.py` | 3 | Local/fixture/platform gate reports |
| Governed direct pipeline | `tests/test_governed_direct_pipeline.py` | 2 | Direct lane packets, realtime signal feed |
| Jarvis operator & protocol | `tests/test_jarvis_operator.py`, `tests/test_jarvis_protocol.py` | 4 | Evolution/forge wraps, modular provider |
| Eligibility & health | `tests/test_alt7_governed_eligibility.py`, `tests/test_app_main_health.py` | 2 | ALT7 eligibility, legacy health snapshot |
| Lab / linguistic | `tests/test_lab_http.py`, `tests/test_linguistic_drift_forecast_engine.py` | 2 | Lab init/status, drift forecast band |

### Top 15 files by failure count

| Failures | File |
|----------|------|
| 11 | `tests/test_api.py` |
| 10 | `tests/test_operator_cognition_coherence_fabric.py` |
| 3 | `tests/test_coherence_fabric_bridge.py` |
| 2 | `tests/test_adaptive_lane_bridge.py` |
| 2 | `tests/test_coherence_fabric_pipeline.py` |
| 2 | `tests/test_forge_shippable_gate.py` |
| 2 | `tests/test_governed_direct_pipeline.py` |
| 2 | `tests/test_jarvis_operator.py` |
| 2 | `tests/test_jarvis_protocol.py` |
| 1 | `tests/test_alt7_governed_eligibility.py` |
| 1 | `tests/test_app_main_health.py` |
| 1 | `tests/test_forge_platform_gate.py` |
| 1 | `tests/test_lab_http.py` |
| 1 | `tests/test_linguistic_drift_forecast_engine.py` |

*(41 failures across 14 files; table lists all failing files.)*

## Post safety fix (detail)

- **Counts:** 41 failed, 1903 passed, 8 skipped, 2 warnings, 20 subtests passed.
- **Delta vs prior:** −82 failures; +86 passed (vs 1817).
- **Safety envelope fix impact:** Large reduction in total failures; remaining work concentrated in API/patch routes, operator-cognition ALT version tests, and coherence-fabric/governed-lane integration — not in the OTEM/substrate/safety-envelope slice.

## Cluster fix pass (2026-06-07)

Targeted the two largest post–safety-fix clusters (21 failures).

| File | Before | After | Root cause / fix |
|------|--------|-------|------------------|
| `tests/test_operator_cognition_coherence_fabric.py` | 10 failed | **0 failed** (46 passed) | Schema drift: runtime is `operator_cognition_coherence_fabric.v1.24`; tests still asserted v1.23 on ALT12–ALT27 plane checks. Updated expectations to v1.24. |
| `tests/test_api.py` | 11 failed | **0 failed** (231 passed) | `forge_repo_governance.finalize_contractor_runtime_action` unpacked 3 values from `project_infi_law.finalize_runtime_action`, which returns 2 (`law_enforcement`, `law_event_log`); `ul_snapshot` already comes from `require_contract`. One lifecycle test also assumed `last_board_event()` was `expiry_review` after chat turns now record `conversation_memory.write` — test now finds the `expiry_review` event in board history. |

Verification:

```text
python -m pytest tests/test_operator_cognition_coherence_fabric.py tests/test_api.py -q --tb=line
```

**277 passed**, 0 failed (~10m).

Full-suite spot-check after cluster pass:

```text
python -m pytest tests/ -q --tb=no
```

**17 failed**, **1927 passed**, 8 skipped (was 41 failed / 1903 passed). Net **−24 failures** on full suite; remaining failures are outside these two files (coherence-fabric bridge, forge gates, jarvis operator, etc.).

## Bridge action pass (2026-06-07)

Targeted the coherence-fabric bridge cluster (~5 failures from missing `action` in test specs).

| File | Before | After | Root cause / fix |
|------|--------|-------|------------------|
| `tests/test_coherence_fabric_bridge.py` | 3 failed | **0 failed** | `_recipe_spec()` omitted `action`; `_execute_spec` KeyError before lane/coherence gates. Added `action`/`action_label`, `_register_test_route()` helper. |
| `tests/test_adaptive_lane_bridge.py` | 2 failed | **0 failed** (+1 new guard test) | Same spec/route fix; prod guard returns genome block for missing `action`. |

Production change: [`src/capability_service_bridge.py`](../../src/capability_service_bridge.py) — early `_build_genome_block(..., "missing bridge action", ...)` instead of KeyError.

Verification:

```text
python -m pytest tests/test_coherence_fabric_bridge.py tests/test_adaptive_lane_bridge.py -q
```

**6 passed**, 0 failed (~30s).

## Genome boot blocker (2026-06-07)

Full re-baseline initially failed at collection (19 errors) because `Alt4Runtime.boot_validate()` runs on `import src.api` before pytest conftest sets `AAIS_GENOME_BOOT=warn`.

Registry errors (initial):

```
immune_resilience_organ.genome.v1.json: governed stage requires proof.bundles
immune_resilience_organ: parent immune_observe_organ does not list immune_resilience_organ in children
immune_resilience_organ: parent policy_gate_organ does not list immune_resilience_organ in children
```

Additional lineage errors surfaced after immune_resilience fix:

```
culture_habit_runtime: parent operator_decision_ledger / jarvis_memory_board missing child ref
workflow_family_* (6): parent plug_adapter_runtime missing child refs
```

JSON fixes (6 genome files):

| File | Change |
|------|--------|
| `governance/subsystem_genomes/immune_resilience_organ.genome.v1.json` | Populated `proof.bundles` with `IMMUNE_RESILIENCE_ORGAN_V1_PROOF.md` |
| `governance/subsystem_genomes/immune_observe_organ.genome.v1.json` | Added `immune_resilience_organ` to `lineage.children` |
| `governance/subsystem_genomes/policy_gate_organ.genome.v1.json` | Added `immune_resilience_organ` to `lineage.children` |
| `governance/subsystem_genomes/operator_decision_ledger.genome.v1.json` | Added `culture_habit_runtime` to `lineage.children` |
| `governance/subsystem_genomes/jarvis_memory_board.genome.v1.json` | Added `culture_habit_runtime` to `lineage.children` |
| `governance/subsystem_genomes/plug_adapter_runtime.genome.v1.json` | Added all six `workflow_family_*` genes to `lineage.children` |

Post-fix: `GenomeEngine.reload()` → `ok True`; `test_api.py` collects 231 tests.

**Note:** Use `python -m pytest` (not bare `pytest`) so local `platform/` package resolves before stdlib `platform`.

## Post bridge + genome boot (remaining failures)

Full suite after both passes:

```text
python -m pytest tests/ -q --tb=no
```

**23 failed**, **1977 passed**, 8 skipped.

Bridge cluster **resolved** (not in failure list). Passed count rose +50 vs cluster pass (1977 vs 1927) because platform tests now collect under `python -m pytest`. Failed count rose +6 vs cluster pass (23 vs 17) — new failures concentrated in genome/mutation verification tests likely sensitive to lineage graph changes.

| Cluster | Test file(s) | Failures | Notes |
|---------|----------------|----------|-------|
| Genome / Alt-4 gate | `tests/test_governance_organs_alt4.py` | 4 | `test_genome_registry_valid`, mutation roundtrip, alt4 gate |
| Mutation verify (MP-*) | `test_*_mutation_MP_*.py` (6 files) | 8 | ALO, NTP, LING, OCCF, OPO, SE verify/apply |
| Coherence fabric pipeline | `tests/test_coherence_fabric_pipeline.py` | 2 | Mock binding / safety halt vs fabric misaligned |
| Forge ship/platform gates | `tests/test_forge_shippable_gate.py`, `tests/test_forge_platform_gate.py` | 3 | Local/fixture/platform gate reports |
| Jarvis protocol | `tests/test_jarvis_protocol.py` | 2 | Modular provider messages/preview |
| Operator cognition (immune) | `tests/test_operator_cognition_coherence_fabric.py` | 2 | ALT10 immune_observe posture/alignment |
| Misc singles | `test_app_main_health`, `test_lab_http`, `test_linguistic_drift_forecast_engine`, `test_adaptive_lane_organ_mutation_MP_ALO_001` | 4 | Health snapshot, lab init, drift band, ALO verify |

### Top files by failure count (post bridge + genome boot)

| Failures | File |
|----------|------|
| 4 | `tests/test_governance_organs_alt4.py` |
| 2 | `tests/test_coherence_fabric_pipeline.py` |
| 2 | `tests/test_forge_shippable_gate.py` |
| 2 | `tests/test_jarvis_protocol.py` |
| 2 | `tests/test_narrative_trust_pack_mutation_MP_NTP_001.py` |
| 2 | `tests/test_operator_cognition_coherence_fabric.py` |
| 1 | each of 7 other files |

*(23 failures across 16 files.)*
