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

## Verification

```bash
make linguistic-predictive-cycle
make meta-linguistic-gate
make linguistic-governance-cycle
make linguistic-remediation-gate
make linguistic-predictive-gate
make linguistic-governance-cycle-gate
python tools/linguistic_cascade_report.py --gene operator_cognition_coherence_fabric
```
