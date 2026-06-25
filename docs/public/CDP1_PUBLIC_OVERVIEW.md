# CDP-1 Public Overview

## What CDP-1 Is

**CDP-1** (Continuity Demonstration Protocol) is the experiment that demonstrates whether corrigibility propagates across stewards.

It answers:

> Does preserved calibration actually improve future judgment?

## What CDP-1 Requires

| Input | Role |
|-------|------|
| CRR-1 | Preserved calibration event |
| CLG-1 | Preserved lineage graph |
| Independent steward (S₂) | Did not experience original contradiction |
| Measurable task | Same contradiction class pre/post |
| Pre/post comparison | Q_pre, Q_post |
| Threshold (τA) | Minimum ΔA for continuity claim |
| Validated receipt | CAA-1 / CXD-1 |

## What CDP-1 Proves

If **ΔA ≥ τA**, then:

- Continuity propagated
- Calibration survived transfer
- Corrigibility regenerated

## Run

```bash
python -m pytest tests/mission006/ -v
```

## Learn More

- [CDP1_CONSTITUTIONAL_SPEC.md](../crk1/continuity/CDP1_CONSTITUTIONAL_SPEC.md)
- [CONTINUITY_OS_WHITEPAPER_v0.1.md](./CONTINUITY_OS_WHITEPAPER_v0.1.md)
- [CEP_OVERVIEW.md](../../sdk/continuity-sdk/CEP_OVERVIEW.md)
