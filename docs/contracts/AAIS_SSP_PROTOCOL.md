# AAIS Subsystem Summoner Pattern (SSP)

Status: **active contract**

CISIV stage: **structure**

## Purpose

SSP is a deterministic pattern that takes raw idea seeds and transforms them into
fully governed subsystem families before any runtime code is written. Cursor runs
SSP on demand via the project skill at `.cursor/skills/subsystem-summoner/`.

This protocol prevents **ghost subsystems** — features referenced in conversation
or docs without schema, concept spec, proof posture, MVP plan, or doc tree wiring.

## Summon Command

```text
Cursor, summon N subsystem families: <seed 1>, <seed 2>, …
```

Alternate triggers: "run SSP on …", "admit concept …"

## Input

N idea seeds — short descriptions such as:

- "Operator lineage graph"
- "Triangulation ledger"
- "Narrative trust pack"

Optional: dependency hints, target subsystem README, proof subdirectory.

## Output (Per Idea)

| Deliverable | Location |
|-------------|----------|
| Concept spec (CISIV concept stage) | `docs/_future/ideas_pending/<NAME>.md` |
| Schema | `schemas/<name>.v1.json` + `docs/_future/ideas_pending/schemas/` copy |
| MVP plan | `docs/_future/ideas_pending/<NAME>_MVP_PLAN.md` |
| Doc tree wiring | Indexes, subsystem READMEs, `AAIS_SUBSYSTEM_SPEC.md` |
| Audit entry | `docs/audit/LOGBOOK.md` |
| Proof posture | §8 in concept spec; claims default `none_yet` |

## Seven-Step Pipeline (SSP + Alt-4)

| Step | Action |
|------|--------|
| 1 | Generate concept spec |
| 2 | Generate schema (canonical + concept-origin copy) |
| 3 | Wire doc tree |
| 4 | Add audit entry (CISIV stage `concept`) |
| 5 | Generate MVP plan |
| 6 | (Optional) Scaffold code stubs — no full logic unless asked |
| 7 | Generate subsystem genome at `governance/subsystem_genomes/<gene>.genome.v1.json` |

Full execution checklist: [.cursor/skills/subsystem-summoner/SKILL.md](../../.cursor/skills/subsystem-summoner/SKILL.md)

## Governance Rule

No subsystem becomes real until it has **all** of:

1. Schema
2. Concept spec
3. Proof posture table
4. MVP plan
5. Doc tree wiring
6. Subsystem genome (Alt-4)

Enforced by `make ssp-gate` and `make genome-gate` (every admitted family has a genome record).

## SSP Alt-4 (Governance-of-Governance)

Alt-4 adds lifecycle contracts, mutation/retirement paths, and the **Subsystem
Genome** meta-schema:

| Artifact | Path |
|----------|------|
| Promotion protocol | [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md) |
| Retirement protocol | [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md) |
| Mutation path | [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md) |
| Subsystem genome | [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md) |
| Meta-schema | [schemas/subsystem_genome.v1.json](../../schemas/subsystem_genome.v1.json) |
| Genome registry | [governance/subsystem_genomes/](../../governance/subsystem_genomes/) |

Gates: `make ssp-gate` + `make genome-gate`

## Alt-4 Runtime Organs

Governance-of-governance protocols are executable at runtime via
`src/governance_organs/`:

| Organ | Module | Role |
|-------|--------|------|
| Genome Engine | `genome_engine.py` | Validates DNA on boot, `make genome-gate`, and capability-bridge calls |
| Promotion Engine | `promotion_engine.py` | Full-auto `concept → prototype → mvp → governed` when gates pass |
| Mutation Engine | `mutation_engine.py` | MP-X apply/rollback with `schemas/deltas/` |
| Retirement Engine | `retirement_engine.py` | 10-step retirement state machine with lineage preservation |

Facade: `Alt4Runtime` in `src/governance_organs/__init__.py`.

Operator guide: [AAIS_ALT4_RUNTIME_OPERATOR_GUIDE.md](./AAIS_ALT4_RUNTIME_OPERATOR_GUIDE.md)

Makefile targets:

```bash
make alt4-gate          # genome-gate + promotion eligibility scan
make alt4-gate-strict   # same, but fail when promotions are pending
make promotion-scan     # dry-run next-stage evaluation for all genes
make promotion-apply    # full-auto apply when eligible
make retirement-scan    # dry-run retirement step report for all genes
make retirement-apply   # apply retirement advance (GENE= STEP= required)
```

Boot hook: Flask (`src/api.py`) and workflow shell (`app/main.py`) call
`Alt4Runtime.boot_validate()` unless `AAIS_GENOME_BOOT=warn`.

Step 7 summon completes when the genome exists **and** runtime organs can enforce
lifecycle transitions without manual registry surgery.

## Alt-5 Summon Wave

Batch-admit new subsystem families via the [subsystem-summoner skill](../../.cursor/skills/subsystem-summoner/SKILL.md).

| Convention | Value |
|------------|-------|
| Batch id | `alt5-summon-wave-YYYY-MM` in LOGBOOK + `activation.batch_id` |
| Initial stage | `concept` — empty `runtime.surface` |
| MVP promotion | `tools/governance/alt5_promote_mvp.py` or Promotion Engine twice (`concept→prototype→mvp`) |
| Gates | `make alt5-gate` — Alt-5 organ gates + `genome-gate` |

Wave 1 (2026-06): `safety_envelope_organ`, `operator_profile_organ`.

Wave 2 (2026-06): `reflection_runtime_organ`, `memory_runtime_organ` (Nova cortex lobes;
batch `alt5-summon-wave-2-2026-06`; promotion via `tools/governance/alt5_promote_wave2_mvp.py`).

All four Alt-5 organs may be promoted `mvp` → `governed` via
`tools/governance/alt5_promote_governed.py` or per-gene `promotion_engine --apply`.

## Activation Rule

Subsystems move through stages per
[AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md):

```text
concept → prototype → mvp → governed
```

Promotion from `docs/_future/ideas_pending/` requires (per
[ideas_pending/README.md](../_future/ideas_pending/README.md)):

1. Spec admitted into `docs/subsystems/`, `docs/runtime/`, or contracts
2. Runtime code backs the claimed behavior
3. Proof packet exists under `docs/proof/` with appropriate claim labels
4. Passing tests, schema validation, and make gate
5. Genome record updated (`governance/subsystem_genomes/<gene>.genome.v1.json`)

## Proof Posture Terminology

At concept admission:

- **`none_yet`** — claim not yet proven; default for implementation targets
- **`asserted`** — schema-coverage or doc-only claims backed by spec + schema

The informal term `asserted_none_yet` maps to **`none_yet`** in proof posture tables.
Do not add a third label enum to schemas or docs.

## Activation Order (Batches)

When admitting N ideas in one pass, assign order by:

1. Fewest dependencies on existing live subsystems first
2. Ideas that other pending ideas depend on before their dependents
3. Record in concept spec §11, MVP plan §8, and LOGBOOK outcome

## Schema Conventions

- JSON Schema draft 2020-12
- `$id`: `<snake_case>.v1`
- Required `{entity}_version` const matching `$id`
- Required `claim_label`: `asserted` | `proven` | `rejected`
- Required `cisiv_stage`: `concept` | `identity` | `structure` | `implementation` | `verification`
- CISIV helpers: [src/cisiv.py](../../src/cisiv.py)

## Golden Examples

| Idea | Concept | MVP plan | Active doc | Proof |
|------|---------|----------|------------|-------|
| CISIV Operator Lineage Console | [CISIV_OPERATOR_LINEAGE_CONSOLE.md](../_future/ideas_pending/CISIV_OPERATOR_LINEAGE_CONSOLE.md) | [CISIV_OPERATOR_LINEAGE_CONSOLE_MVP_PLAN.md](../_future/ideas_pending/CISIV_OPERATOR_LINEAGE_CONSOLE_MVP_PLAN.md) | [UL_LINEAGE_CONSOLE.md](../runtime/UL_LINEAGE_CONSOLE.md) | [UL_LINEAGE_CONSOLE_V1_PROOF.md](../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md) |
| Forensic Triangulation Ledger | [FORENSIC_TRIANGULATION.md](../_future/ideas_pending/FORENSIC_TRIANGULATION.md) | [FORENSIC_TRIANGULATION_MVP_PLAN.md](../_future/ideas_pending/FORENSIC_TRIANGULATION_MVP_PLAN.md) | [TRIANGULATION.md](../subsystems/forensics/TRIANGULATION.md) | [TRIANGULATION_V1_PROOF.md](../proof/forensics/TRIANGULATION_V1_PROOF.md) |
| Narrative Trust Pack | [NARRATIVE_TRUST_PACK.md](../_future/ideas_pending/NARRATIVE_TRUST_PACK.md) | [NARRATIVE_TRUST_PACK_MVP_PLAN.md](../_future/ideas_pending/NARRATIVE_TRUST_PACK_MVP_PLAN.md) | [NARRATIVE_TRUST_PACK.md](../subsystems/storyforge/NARRATIVE_TRUST_PACK.md) | [NARRATIVE_TRUST_PACK_V1_PROOF.md](../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md) |

## Related

- [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md)
- [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md)
- [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md)
- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)
- [AAIS_MODULE_GOVERNANCE_PROTOCOL.md](./AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
- [AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md)
- [AAIS_DOC_PROTOCOL.md](./AAIS_DOC_PROTOCOL.md)
- [ideas_pending/README.md](../_future/ideas_pending/README.md)
