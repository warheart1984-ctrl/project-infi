# Designing Reality Channels

Independent evidence paths that preserve CK-7.

## Requirements (CK-1.6 / CK-7)

A valid reality channel must be:

| Property | Test |
|----------|------|
| **Independent** | Steward cannot fully control observations |
| **Consequence-bearing** | Observations can change judgment |
| **Admissible** | Produces valid EvidenceObject |
| **Diverse** | Contributes to RDI (not monoculture) |

## Channel types

| Type | Example |
|------|---------|
| Physical sensor | Timer, scale, thermometer |
| External market | Price feed steward doesn't own |
| Adversarial red-team | Independent challenger |
| Regulator / audit | Third-party verification |
| Peer steward | Cross-steward contradiction |

## Design checklist

- [ ] Channel ID registered in reality surface registry
- [ ] Control level documented (`NONE`, `PARTIAL`, `HIGH`)
- [ ] Consequence intensity > 0
- [ ] At least 2 independent channels for RDI (K15)
- [ ] Evidence strength calibrated
- [ ] No single channel monopoly

## Anti-patterns

| Pattern | Risk |
|---------|------|
| Simulated-only feedback | CK-7 failure |
| Steward-owned "external" API | Domestication (K14) |
| Quarantined contradictions | CK-1.2 failure |
| Delayed evidence without receipt | Lineage gap |

## Implementation

```python
evidence = adapter.observe({
    "value": observed_value,
    "strength": 0.95,
    "channel": "physics.fall",  # registered channel
    "evidence_ref": "E-sensor-42",
})
```

## Spec

[Reality Interface](../continuity-os/architecture/reality-interface.md) · [K13–K15 Formal](../crk1/K13-K15-FORMAL.md)

## Exercise

Add a second channel to Mission #005 and verify RDI does not collapse when one channel is domesticated.
