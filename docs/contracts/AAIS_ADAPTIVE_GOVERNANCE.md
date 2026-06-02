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
make alt6-governed-gate   # Alt-6 fabric minimum → governed eligibility
```

## Governed Lane Fabric (Alt-6)

Adaptive lanes reach **governed** when the organ and platform fabric genes carry
`operator_lanes` DNA and runtime enforcement is proven.

### Fabric minimum genes

| Gene | Role |
|------|------|
| `adaptive_lane_organ` | wake / merge / resolve organ |
| `operator_profile_organ` | authority lane source |
| `capability_service_bridge` | execute-path enforcement |
| `recipe_module` | Tier 5 pilot + contextual_gates |
| `governed_direct_pipeline` | direct vs service lane fabric |

Each gene MUST define `operator_lanes` with `lane_id`, `weight`, and non-empty
`capabilities`.

### Awakened registry checklist

After `wake_adaptive_lanes()`:

- [ ] `awakened == true`
- [ ] `genes_with_lanes` contains all five fabric genes
- [ ] `authority_lane == "operator"`
- [ ] `lane_count >= 1` with merged `operator` lane

### Governed promotion checklist

| Requirement | Evidence |
|-------------|----------|
| Fabric DNA on all five genes | `make genome-gate` |
| Awakened registry valid | `tools/governance/check_alt6_governed_eligibility.py` |
| Lane organ gate | `make adaptive-lane-gate` |
| Tier 5 health | `make tier5-gate` |
| Governed proof (majority `proven`) | `docs/proof/platform/ADAPTIVE_LANE_GOVERNED_PROOF.md` |
| Maturity-tagged invariants on organ | `adaptive_lane_organ` genome |
| Bridge policy-cap block proven | pytest bridge + lane tests |

Promotion script: `tools/governance/alt6_promote_governed.py`

## Related

- [AAIS_SSP_PROTOCOL.md](./AAIS_SSP_PROTOCOL.md)
- [src/governance_organs/adaptive_engine.py](../../src/governance_organs/adaptive_engine.py)
