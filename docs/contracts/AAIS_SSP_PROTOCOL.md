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

## Six-Step Pipeline

| Step | Action |
|------|--------|
| 1 | Generate concept spec |
| 2 | Generate schema (canonical + concept-origin copy) |
| 3 | Wire doc tree |
| 4 | Add audit entry (CISIV stage `concept`) |
| 5 | Generate MVP plan |
| 6 | (Optional) Scaffold code stubs — no full logic unless asked |

Full execution checklist: [.cursor/skills/subsystem-summoner/SKILL.md](../../.cursor/skills/subsystem-summoner/SKILL.md)

## Governance Rule

No subsystem becomes real until it has **all** of:

1. Schema
2. Concept spec
3. Proof posture table
4. MVP plan
5. Doc tree wiring

Enforced by `make ssp-gate` (`tools/governance/check_ssp_completeness.py`).

## Activation Rule

Subsystems move through stages:

```text
concept → prototype → mvp → governed
```

Promotion from `docs/_future/ideas_pending/` requires (per
[ideas_pending/README.md](../_future/ideas_pending/README.md)):

1. Spec admitted into `docs/subsystems/`, `docs/runtime/`, or contracts
2. Runtime code backs the claimed behavior
3. Proof packet exists under `docs/proof/` with appropriate claim labels
4. Passing tests, schema validation, and make gate

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

- [AAIS_MODULE_GOVERNANCE_PROTOCOL.md](./AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
- [AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md)
- [AAIS_DOC_PROTOCOL.md](./AAIS_DOC_PROTOCOL.md)
- [ideas_pending/README.md](../_future/ideas_pending/README.md)
