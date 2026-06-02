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
make alt7-gate            # Alt-7 coherence fabric + fabric dependency
make alt7-governed-gate   # Alt-7 governed eligibility + bridge enforcement
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

## Alt-6.1 Lane Mutation (MP-X)

Wake is **read-only**. Any change to `governance.operator_lanes` DNA requires an MP-X
proposal per [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md).

| Change type | Path | Examples |
|-------------|------|----------|
| **Lane mutation** | MP-X on gene(s) + fabric re-validation | Add capability, add lane, adjust weight |
| **Wake refresh** | `Tier5Governance.wake_lanes()` after MP-X apply | Re-merge DNA into `.runtime/governance/adaptive_lanes.json` |
| **Promotion** | Promotion Engine stage bump | concept → governed (not lane DNA) |
| **Runtime edit** | **Forbidden** | Direct edits to `adaptive_lanes.json` |

### Lane mutation rules

- `backward_compatible: true` required
- Affected genes MUST pass `genome_engine` `operator_lanes` validation
- If any **fabric minimum** gene mutates lanes, post-apply MUST pass `make alt6-governed-gate`
- `authority_lane` MUST remain sourced from `operator_profile_organ` — lane mutations
  must not override profile authority
- Frozen schemas require explicit LOGBOOK unfreeze note per mutation path contract

### Golden path

| Artifact | Location |
|----------|----------|
| Proposal | `docs/_future/mutations/MP-ALO-001.md` |
| Lane delta | `schemas/deltas/adaptive_lane_organ_MP-ALO-001.json` |
| Gate | `make adaptive-lane-mutation-gate` |

```bash
make adaptive-lane-mutation-gate
python -m src.governance_organs.mutation_engine --gene adaptive_lane_organ --mp-id MP-ALO-001 --verify
python -m src.governance_organs.mutation_engine --gene adaptive_lane_organ --mp-id MP-ALO-001 --apply --invariant "..."
```

## Alt-7 Operator–Cognition Coherence Fabric

Read-only cross-plane snapshot joining profile, lanes, and envelope posture.

| Plane | Governed source | Stabilizes |
|-------|-----------------|------------|
| Profile | `operator_profile_organ` | Identity, `authority_lane`, operator supremacy |
| Lanes | `adaptive_lane_organ` + fabric `operator_lanes` | Weighted routing, policy-cap authorization |
| Envelopes | bridge / pipeline / memory board / safety envelope status | Turn-scoped `governance_mode`, `claim_label`, `phase_context` |

**Runtime surface (MVP):**

| Kind | Path |
|------|------|
| module | `src/operator_cognition_coherence_fabric.py` |
| API | `GET /api/jarvis/coherence-fabric/status` |
| gate | `make coherence-fabric-gate`, `make alt7-gate` |

**Coherence invariants (governed):**

1. Profile `authority_lane` is the sole authority source for lane policy-cap checks — **constitutional**
2. Envelope `governance_mode` and lane resolution MUST agree before bridge execute on policy capabilities — **constitutional**
3. Envelope snapshots are read-only; lane/profile drift triggers auditable block — **stable**
4. Coherence projection remains read-only — informs voice, not routing authority — **stable**

**Governed promotion checklist**

| Requirement | Evidence |
|-------------|----------|
| Alt-6 fabric healthy | `check_alt6_governed_eligibility` via alt7-governed-gate |
| Coherence snapshot aligned | `build_coherence_fabric_status()` |
| Bridge execute enforcement | `tests/test_coherence_fabric_bridge.py` |
| Governed proof | `OPERATOR_COGNITION_COHERENCE_FABRIC_GOVERNED_PROOF.md` |
| Constitutional invariants | genome maturity tags |

Promotion MVP: `tools/governance/alt7_promote_mvp.py`

Promotion governed: `tools/governance/alt7_promote_governed.py`

```bash
make alt7-gate
make alt7-governed-gate
python tools/governance/alt7_promote_governed.py
```

Tier 5 health includes `coherence_fabric_aligned` from the snapshot builder.

## Related

- [AAIS_SSP_PROTOCOL.md](./AAIS_SSP_PROTOCOL.md)
- [src/governance_organs/adaptive_engine.py](../../src/governance_organs/adaptive_engine.py)
