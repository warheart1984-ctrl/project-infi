# AAIS Meta-Linguistic Governance

Status: **active contract**

CISIV stage: **structure**

Governance-of-governance for mythic and engineering linguistic alignment across all subsystem families.

## Subordinate contracts

- [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](./AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md) — Waves 0–8 naming protocol
- [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md) — `linguistic_layer` MP-X
- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md) — genome `ssp` linguistic fields

## Registry

Instance: [governance/meta_linguistic_registry.v1.json](../../governance/meta_linguistic_registry.v1.json)

Schema: [schemas/meta_linguistic_registry.v1.json](../../schemas/meta_linguistic_registry.v1.json)

## Policy modes

| Mode | Behavior |
|------|----------|
| `observe` | Gates run; high drift and cascade issues emit warnings only |
| `enforce` | `meta-linguistic-gate` fails on high drift without remediation playbook; cascade_ack required when policy enabled |

## Orchestration

Facade: `LinguisticGovernanceEngine` in [src/governance_organs/linguistic_governance_engine.py](../../src/governance_organs/linguistic_governance_engine.py)

```bash
make meta-linguistic-gate
```

Gate sequence:

1. `naming-gate`
2. `naming-genome-gate`
3. `linguistic-mutation-gate`
4. `linguistic-drift-gate` (refreshes drift report)

Optional Alt-4 integration: set `AAIS_META_LINGUISTIC_GATE=1` before `make alt4-gate`.

## Wave 9 — Remediation playbooks

Directory: [governance/linguistic_remediations/](../../governance/linguistic_remediations/)

Generator: `python tools/governance/generate_linguistic_remediations.py --min-band medium`

Gate: `make linguistic-remediation-gate`

## Wave 10 — Lineage cascade

Policy: [governance/linguistic_cascade_policy.v1.json](../../governance/linguistic_cascade_policy.v1.json)

Report: `python tools/linguistic_cascade_report.py --gene <parent_gene>`

Linguistic deltas may include optional `cascade_ack: [child genes]` when `block_apply_without_cascade_ack` is true.

## Wave 11 — Self-optimizing governance cycle

Policy: [governance/linguistic_governance_cycle_policy.v1.json](../../governance/linguistic_governance_cycle_policy.v1.json)

Artifacts: [governance/linguistic_governance_cycles/](../../governance/linguistic_governance_cycles/)

Engine: `LinguisticGovernanceCycleEngine` — closed loop:

1. Run meta-linguistic gates (optional skip)
2. Refresh drift report
3. Generate remediation playbooks (adaptive `min_band`)
4. Cascade-scan high-fanout parents
5. Compare metrics to previous cycle; emit optimization recommendations
6. Persist cycle report and update registry

```bash
make linguistic-governance-cycle
make linguistic-governance-cycle-gate
```

`auto_tune_policy` in cycle policy (default `false`) — when `true`, may promote registry to `enforce` after sustained high drift.

## Wave 12 — Predictive governance cycle

Policy: [governance/linguistic_predictive_governance_policy.v1.json](../../governance/linguistic_predictive_governance_policy.v1.json)

Forecast report: [governance/linguistic_drift_forecast.v1.json](../../governance/linguistic_drift_forecast.v1.json)

Preemptive playbooks: [governance/linguistic_preemptive_remediations/](../../governance/linguistic_preemptive_remediations/)

Engine: `LinguisticPredictiveGovernanceEngine` — anticipates drift via snapshot trajectory, latent alignment, MP-LING pressure, parent forecast, and ecosystem trend.

```bash
make linguistic-predictive-cycle
make linguistic-predictive-gate
make linguistic-governance-cycle
```

Wave 11 consumes forecast when `use_forecast_in_cycle` is true in cycle policy.

## Wave 13 — Calibrating + prescriptive cycle

Calibration policy: [governance/linguistic_forecast_calibration_policy.v1.json](../../governance/linguistic_forecast_calibration_policy.v1.json)

Calibration report: [governance/linguistic_forecast_calibration.v1.json](../../governance/linguistic_forecast_calibration.v1.json)

Governance queue: [governance/linguistic_governance_queue.v1.json](../../governance/linguistic_governance_queue.v1.json)

Engines:

- `LinguisticForecastCalibrationEngine` — score prior forecast vs current drift; weight recommendations
- `build_governance_queue` — unified operator backlog
- `LinguisticFullGovernanceCycleEngine` — calibrate → predict → react → queue → gates

```bash
make linguistic-calibration-cycle
make linguistic-governance-queue
make linguistic-full-governance-cycle
make linguistic-calibration-gate
```

Wave 12 may consume `recommended_weights` when `use_calibration_weights` is true.

## Wave 14 — Attested closed-loop + queue work orders

Forecast archive: [governance/linguistic_forecast_archive/](../../governance/linguistic_forecast_archive/)

Work orders: [governance/linguistic_governance_work_orders/](../../governance/linguistic_governance_work_orders/)

Attestation: [governance/linguistic_governance_attestation.v1.json](../../governance/linguistic_governance_attestation.v1.json)

Cadence policy: [governance/linguistic_governance_cadence_policy.v1.json](../../governance/linguistic_governance_cadence_policy.v1.json)

Engines:

- `archive_forecast_before_write` / `load_prior_forecast_for_calibration` — same-session calibration fix
- `sync_work_orders_from_queue` — operator execution posture (`pending` | `acknowledged` | `completed` | `deferred`)
- `build_attestation` / `write_attestation` — unified health digest and `closed_loop_score`

```bash
make linguistic-work-order-sync
make linguistic-governance-attestation
make linguistic-attestation-gate
make linguistic-work-order-gate
```

Release 24 read-only organs: forecast calibration, governance queue, full governance cycle, governance attestation (`make alt24-gate`).

## Verification

```bash
make linguistic-full-governance-cycle
make linguistic-calibration-cycle
make linguistic-governance-queue
make linguistic-predictive-cycle
make meta-linguistic-gate
make linguistic-governance-cycle
make linguistic-remediation-gate
make linguistic-predictive-gate
make linguistic-calibration-gate
make linguistic-governance-cycle-gate
python tools/linguistic_cascade_report.py --gene operator_cognition_coherence_fabric
```
