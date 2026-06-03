# AAIS Subsystem Mutation Path

Status: **active contract**

CISIV stage: **structure**

SSP Alt-4: evolve subsystem families in place without replacement.

Parent: [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md)

## Purpose

**Mutation** is evolution without retirement. Use when expanding capability while
preserving identity gene name and backward compatibility.

## Mutation Triggers

| Trigger | Typical deliverable |
|---------|---------------------|
| Schema expansion | Additive fields in new minor schema or `$defs` |
| New invariants | Genome `governance.invariants[]` + tests |
| New runtime organ | Additional `runtime.surface[]` entry |
| New cross-subsystem links | Genome `lineage.parents` / `children` update |
| New governance rules | Additional `governance.contracts[]` entry |
| **Lane DNA change** | MP-X with `mutation_kind: lane_dna` + `operator_lanes` delta (Alt-6.1) |
| **Coherence invariant** | MP-X with `mutation_kind: coherence_invariant` on coherence fabric (Alt-7.1) |
| **Profile invariant** | MP-X with `mutation_kind: profile_invariant` on `operator_profile_organ` (Alt-7.2) |

## Mutation Steps

Execute in order:

| Step | Action |
|------|--------|
| 1 | Create mutation proposal **MP-X** (document under `docs/_future/mutations/` or LOGBOOK) |
| 2 | Add mutation schema delta (`schemas/deltas/<gene>_MP-X.json` or draft v1.1) |
| 3 | Add mutation invariants to genome `governance.invariants[]` |
| 4 | Add mutation tests (`tests/test_<gene>_mutation_MP-X.py` or extend existing) |
| 5 | Add mutation proof bundle (`docs/proof/<area>/<NAME>_MP-X_PROOF.md`) |
| 6 | Run mutation gate `make <gene>-mutation-gate` (when defined) or `make genome-gate` |
| 7 | Promote subsystem to next **minor** version in genome `identity.version` |
| 8 | Append to genome `mutation.history[]` with `status: promoted` |

## Mutation Proposal Format (MP-X)

```markdown
# MP-<ID>: <Gene> — <Title>

- gene: <subsystem gene>
- status: proposed | schema_delta | tests_added | proof_pending | promoted | reverted
- backward_compatible: true | false (must be true to proceed)
- schema_delta_ref: schemas/deltas/...
- affected_subsystems: []
```

Lane mutations (Alt-6.1) add optional fields:

```markdown
- mutation_kind: lane_dna
- operator_lanes_delta_ref: schemas/deltas/<gene>_MP-<ID>.json
- fabric_genes: [adaptive_lane_organ, ...]
- post_apply_wake: true
- post_apply_gate: alt6-governed-gate
```

Coherence mutations (Alt-7.1) add optional fields:

```markdown
- mutation_kind: coherence_invariant
- post_apply_gate: alt7-governed-gate
- fabric_genes: [operator_cognition_coherence_fabric, ...]
- post_apply_snapshot_check: true
```

Fabric lane DNA mutations SHOULD set `post_apply_gate: alt7-governed-gate` in addition to
`alt6-governed-gate` when `fabric_genes` intersect the fabric minimum set.

Profile mutations (Alt-7.2) add optional fields:

```markdown
- mutation_kind: profile_invariant
- post_apply_gate: operator-profile-gate
- post_apply_snapshot_check: true
```

`profile_invariant` apply also runs `alt7-governed-gate`.

Record in LOGBOOK when promoted.

## Mutation Rules

| Rule | Enforcement |
|------|-------------|
| Backward compatible | Existing fixtures and gates MUST pass without modification |
| No break governed dependents | Genomes listing this gene as parent MUST be re-validated |
| Reversible until proof passes | Revert genome `mutation.history` entry to `reverted` if gate fails |
| Frozen schema | Mutations on `schema.frozen: true` require explicit unfreeze LOGBOOK entry |

## Genome `mutation.history` Entry

```json
{
  "proposal_id": "MP-LINEAGE-001",
  "status": "promoted",
  "schema_delta_ref": "schemas/deltas/ul_lineage_graph_MP-LINEAGE-001.json",
  "notes": "Added memory_board lane emitter invariant"
}
```

## Gates

```bash
make genome-gate
make ssp-gate
make <gene>-gate
# optional:
make <gene>-mutation-gate
```

## Related

- [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md)
- [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md)
- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)
