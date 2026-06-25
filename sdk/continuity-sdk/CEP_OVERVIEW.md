# CEP — Continuity Experimental Platform

## Purpose

The SDK is not a developer toolkit. It is a **scientific instrument** for running **CDP-1** experiments.

## CEP Components

### 1. Experiment Harnesses

| Harness | Module |
|---------|--------|
| Pre-measurement | `harness/cdp1_experiment.py` |
| Lineage replay | `CDP1Steward.replay_lineage()` |
| Post-measurement | `harness/cdp1_experiment.py` |
| ΔA computation | `harness/metrics.py` |
| CAA-1 builder | `src/crk1/caa1_assimilation.py` |
| Governance validator | `validate_cdp1_run()` |

### 2. Benchmark Library

| Category | Location |
|----------|----------|
| Logical contradiction tasks | `experiments/success/`, `experiments/failure/hidden_contradiction/` |
| Predictive calibration tasks | `experiments/success/calibration_replay/` |
| Interpretive calibration tasks | Mission #005 lineage demos |
| Governance-aligned tasks | `experiments/failure/governance_bypass/` |

### 3. Failure Mode Library

| Mode | Demo |
|------|------|
| Missing CRR-1 | `experiments/failure/missing_crr/` |
| Broken CLG-1 | `experiments/failure/broken_lineage/` |
| Corrupted lineage | `experiments/failure/corrupted_evidence/` |
| Fake isolation | `experiments/failure/assimilation_redteam/` |
| Threshold gaming | `assimilation_redteam/delta_mismatch.test.ts` |
| Contradiction-class mismatch | Mission manifest binding |

See [cdp1_adversarial_suite.md](./experiments/failure/cdp1_adversarial_suite.md).

### 4. Multi-Steward Replication Tools

- Steward isolation verifier — `compute_isolation_proof()`
- Steward diversity analyzer — [CDP1_MULTI_STEWARD_PROTOCOL.md](../../docs/crk1/mission-006/CDP1_MULTI_STEWARD_PROTOCOL.md)
- Cross-steward ΔA comparison — governance replication framework

### 5. Reporting Tools

- Experiment logs — `CDP1RunResult.to_dict()`
- Validation reports — `validate_cdp1_run()`
- Reproduction bundles — [MISSION-006-REPRODUCTION-BUNDLE.md](../../docs/crk1/mission-006/MISSION-006-REPRODUCTION-BUNDLE.md)

## CEP Philosophy

Every demo must answer a **falsifiable question**:

- Does reconstruction improve prediction?
- Does removing CRR-1 reduce calibration?
- Do independent stewards converge?
- Which preserved artifacts matter?

CEP turns Continuity OS into an experimental science.

## Quick Start

```python
from sdk.continuity_sdk.harness.cdp1_experiment import CDP1Experiment, validate_cdp1_run
```

```bash
python -m pytest sdk/continuity-sdk/tests tests/mission006/ -v
cd sdk/continuity-sdk && npm test
```

## Related

- [CDP1_CONSTITUTIONAL_SPEC.md](../../docs/crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md)
- [CONTINUITY_EXPERIMENT_CARD.md](./docs/CONTINUITY_EXPERIMENT_CARD.md)
