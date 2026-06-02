# AAIS Adaptive Governance (Tier 5)

Status: **active contract**

CISIV stage: **structure**

Parent: [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)

## Purpose

Tier 5 adds **adaptive** governance on top of Alt-4 lifecycle engines: maturity-tagged
invariants, operator-weighted lanes, contextual gates, and self-auditing health reports.

Alt-4 engines remain authoritative for promotion, retirement, mutation, and genome DNA.

## Dynamic Invariants

Invariants may be plain strings (legacy) or objects:

```json
{ "text": "...", "maturity": "emergent" | "stable" | "constitutional" }
```

Governed promotion requires tests for **stable** and **constitutional** invariants only.

## Operator-Weighted Lanes

```json
"operator_lanes": [
  { "lane_id": "operator", "weight": 1.0, "capabilities": ["approve_policy_changes"] }
]
```

Aligned with operator supremacy in Jarvis runtime.

## Contextual Gates

```json
"contextual_gates": [
  {
    "gate_id": "recipe_mission_flow",
    "activate_on": ["operator_runtime", "recipe_mission"],
    "make_target": "recipe-module-gate"
  }
]
```

Evaluated in capability bridge when `runtime_context` and `capability_id` match.

## Self-Auditing

`AdaptiveEngine.health_check()` writes `.runtime/governance/tier5_health.json` with:

- genome registry count and stage histogram
- pending promotions
- open MP-X proposals
- retirement state summary

## Gates

```bash
make tier5-gate
```

## Related

- [AAIS_SSP_PROTOCOL.md](./AAIS_SSP_PROTOCOL.md)
- [src/governance_organs/adaptive_engine.py](../../src/governance_organs/adaptive_engine.py)
