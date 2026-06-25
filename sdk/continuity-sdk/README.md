# Continuity SDK — Continuity Experimental Platform (CEP)

**Not an API.** CEP is a **scientific instrument** for running **CDP-1** (Continuity Demonstration Protocol) experiments.

See [CEP_OVERVIEW.md](./CEP_OVERVIEW.md) and [CDP1_CONSTITUTIONAL_SPEC.md](../../docs/crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md).

## Purpose

External engineers can challenge the architecture without accepting theory on faith. Each experiment ends with a **falsifiable question** and verifiable artifacts (GRR-1, CRR-1, CLG-1, CAA-1).

## Layout

```text
sdk/continuity-sdk/
├── CEP_OVERVIEW.md
├── README.md
├── docs/CONTINUITY_EXPERIMENT_CARD.md
├── crk1/receipts/caa1.ts
├── experiments/
│   ├── success/
│   └── failure/
│       ├── assimilation_redteam/
│       └── cdp1_adversarial_suite.md
├── harness/
│   ├── cdp1_experiment.py    # canonical CDP-1 engine
│   └── assimilation.ts
├── schemas/
├── tests/
└── utils/
```

## Quick start

From repository root:

```bash
python -m pytest tests/mission006/ sdk/continuity-sdk/tests -v
```

Run CDP-1 via Mission #006:

```bash
python -c "from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation; r=run_mission_006_calibration_assimilation(); print(r.to_dict())"
```

TypeScript red-team:

```bash
cd sdk/continuity-sdk && npm install && npm test
```

## Constitutional layers

```
K-INFINITY → CAA-1/CDP-1 → CLG-1 → CRR-1 → GRR-1 → R0
```

## Experiments

| Demo | Question |
|------|----------|
| calibration_replay | Did prediction improve after correction? |
| lineage_only_reconstruction | Can S₂ reconstruct from CLG-1 alone? |
| multi_steward_assimilation | Do independent stewards converge after replay? |
| hidden_contradiction | Does CRC-3 detect hidden contradictions? |
| missing_crr | Does continuity collapse without CRR-1? |

## Related

- Python runtime: `src/crk1/`
- CDP-1 spec: `docs/crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md`
- Public overview: `docs/public/CDP1_PUBLIC_OVERVIEW.md`
- Schemas: `fixtures/crk1/`
