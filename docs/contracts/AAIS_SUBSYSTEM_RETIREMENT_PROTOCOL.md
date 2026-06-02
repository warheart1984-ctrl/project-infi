# AAIS Subsystem Retirement Protocol

Status: **active contract**

CISIV stage: **structure**

SSP Alt-4: safe removal and deprecation of subsystem families without governance rot.

Parent: [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md)

## Purpose

A subsystem may be **retired** when it is superseded, obsolete, unused, or poses
forensic or security risk. Runtime code MUST NOT be removed until retirement proof
and dependent migration are complete.

## Retirement Triggers

| Trigger | Example |
|---------|---------|
| Superseded | Successor subsystem genome lists `retirement.successor_gene` |
| Schema obsolete | Frozen schema replaced by new major version via mutation path |
| Runtime unused | No emissions to `.runtime/<organ>/` for two stable releases |
| Governance replaced | Contract doc superseded by new law surface |
| Security / forensic risk | Immune protocol or triangulation flags critical drift |

## Retirement Steps

Execute in order:

| Step | Action |
|------|--------|
| 1 | Mark subsystem `deprecated` in [AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md) |
| 2 | Freeze schema version (`schema.frozen: true` in genome) |
| 3 | Freeze API (document freeze date in active doc) |
| 4 | Add retirement audit entry to [LOGBOOK.md](../audit/LOGBOOK.md) |
| 5 | Move docs to [docs/_retired/](../_retired/) |
| 6 | Set genome `identity.stage: deprecated`; update `retirement.path` |
| 7 | Remove from SSP summon table (`ssp.summon_eligible: false`) |
| 8 | Remove from activation order (genome `activation.order: -1` or omit from batch) |
| 9 | Add compatibility shim (optional) — genome `retirement.shim_required: true` |
| 10 | Remove runtime code **only after 2 stable releases** with shim in place |

## Retirement Proof

A subsystem **cannot** be removed until:

| Requirement | Evidence |
|-------------|----------|
| Retirement proof bundle | `docs/proof/<area>/<NAME>_RETIREMENT_PROOF.md` |
| Dependent migration | All genomes listing this gene in `lineage.parents` updated |
| Gates pass | `make genome-gate` + subsystem gate green on shim path |
| LOGBOOK sign-off | CISIV stage `verification` |

Proof bundle MUST include:

1. Incident / retirement ID
2. Trigger and rationale
3. Migration checklist (dependent subsystems)
4. Shim verification commands
5. Claim posture table (all `proven` before code removal)

## Genome Updates

```json
{
  "identity": { "stage": "deprecated" },
  "retirement": {
    "path": "docs/_retired/<gene>/README.md",
    "successor_gene": "<optional>",
    "shim_required": true
  },
  "ssp": { "summon_eligible": false }
}
```

Final stage after doc/runtime removal: `identity.stage: retired`.

## SSP Summon Table

Retired subsystems MUST NOT appear in:

- `AAIS_SUBSYSTEM_SPEC.md` §9 Concept Pending (summon targets)
- `.cursor/skills/subsystem-summoner/examples/` active summon list
- `governance/subsystem_genomes/` with `summon_eligible: true`

## Related

- [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md)
- [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md)
- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)
- [docs/_retired/README.md](../_retired/README.md)
