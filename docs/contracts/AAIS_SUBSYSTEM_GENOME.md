# AAIS Subsystem Genome

Status: **active contract**

CISIV stage: **structure**

SSP Alt-4 crown jewel: the meta-schema that defines what a subsystem **is**.

## Purpose

The **Subsystem Genome** is governance-of-governance. Every admitted subsystem
family carries a genome record validated against
[subsystem_genome.v1.json](../../schemas/subsystem_genome.v1.json).

The genome gate (`make genome-gate`) is the DNA validator for AAIS — no subsystem
may violate required genes, miss proof bundles, or break lineage symmetry among
registered families.

## Genome Fields

| Gene block | Field | Required | Description |
|------------|-------|----------|-------------|
| `identity` | `gene` | yes | Unique snake_case subsystem name |
| `identity` | `version` | yes | Semantic version (e.g. `1.0.0-mvp`) |
| `identity` | `stage` | yes | `concept` \| `prototype` \| `mvp` \| `governed` \| `deprecated` \| `retired` |
| `governance` | `contracts[]` | yes | Governance doc paths |
| `governance` | `invariants[]` | yes | Minimal invariants (non-empty) |
| `schema` | `ref` | yes | Canonical schema path |
| `schema` | `frozen` | no | `true` when schema/API frozen (governed+) |
| `runtime` | `surface[]` | yes | CLI, API, UI, tools, gates (empty at concept) |
| `proof` | `bundles[]` | yes | Proof artifact paths (may be empty at concept) |
| `proof` | `posture` | yes | `asserted` \| `prototype` \| `mvp` \| `governed` |
| `proof` | `target_bundles[]` | no | Planned proof paths at concept |
| `lineage` | `parents[]` | yes | Subsystem genes this depends on |
| `lineage` | `children[]` | yes | Subsystem genes that depend on this |
| `activation` | `order` | yes | Integer activation order in batch |
| `retirement` | `path` | no | Retirement doc path when deprecated |
| `mutation` | `history[]` | yes | List of MP-X mutation proposals |
| `ssp` | `concept_spec`, `mvp_plan`, `active_doc` | no | SSP artifact cross-links |
| `ssp` | `summon_eligible` | no | `false` when retired from summon table |
| `ssp` | `engineering_class` | no | PascalCase `<Domain><Function><Role>` — validated by `make naming-genome-gate` |
| `ssp` | `mythic_label` | no | Short mythic label for operator docs (comments only in code) |
| `ssp` | `linguistic_version` | no | Semver; bump when mythic/engineering text changes via MP-X |

## Registry Location

Instance files:

```text
governance/subsystem_genomes/<gene>.genome.v1.json
```

Index: [governance/subsystem_genomes/README.md](../../governance/subsystem_genomes/README.md)

## Stage Constraints (Enforced by Gate)

| Stage | `runtime.surface` | `proof.posture` | `proof.bundles` |
|-------|-------------------|-----------------|-----------------|
| `concept` | MUST be `[]` | MUST be `asserted` | May be `[]`; use `target_bundles` |
| `prototype` | ≥1 entry, prefer `isolated: true` | `prototype` | ≥1 prototype proof |
| `mvp` | ≥1 integrated entry | `mvp` or `governed` | ≥1 full proof bundle |
| `governed` | stable surface | `governed` | ≥1 proven bundle |

## Genome Enforcement

```bash
make genome-gate
```

Script: [tools/governance/check_subsystem_genome.py](../../tools/governance/check_subsystem_genome.py)

Checks:

- Every registry genome validates against meta-schema required fields
- Referenced schemas, contracts, and proof bundles exist on disk
- No missing invariants or empty governance blocks
- Lineage symmetry among registered genomes (parent/child reciprocity)
- Concept-stage genomes have no runtime surface
- MVP-stage genomes have proof bundles and gates
- Retired genes have `summon_eligible: false`

## Creating a Genome on Summon

SSP Step 7 (Alt-4): after MVP plan, write
`governance/subsystem_genomes/<gene>.genome.v1.json` at `stage: concept`.

Template: copy structure from
[cisiv_operator_lineage_console.genome.v1.json](../../governance/subsystem_genomes/cisiv_operator_lineage_console.genome.v1.json)
and adjust fields.

## Golden Genomes

| Gene | Stage | File |
|------|-------|------|
| `cisiv_operator_lineage_console` | mvp | [cisiv_operator_lineage_console.genome.v1.json](../../governance/subsystem_genomes/cisiv_operator_lineage_console.genome.v1.json) |
| `forensic_triangulation` | mvp | [forensic_triangulation.genome.v1.json](../../governance/subsystem_genomes/forensic_triangulation.genome.v1.json) |
| `narrative_trust_pack` | mvp | [narrative_trust_pack.genome.v1.json](../../governance/subsystem_genomes/narrative_trust_pack.genome.v1.json) |

## Related

- [AAIS_SSP_PROTOCOL.md](./AAIS_SSP_PROTOCOL.md)
- [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md)
- [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md)
- [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md)
- [schemas/subsystem_genome.v1.json](../../schemas/subsystem_genome.v1.json)
