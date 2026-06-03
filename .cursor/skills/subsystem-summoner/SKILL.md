---
name: subsystem-summoner
description: >-
  Run the Subsystem Summoner Pattern (SSP) and SSP Alt-4 on AAIS idea seeds. Use
  when the user says "summon N subsystem families", "run SSP on", "admit concept",
  or asks for concept specs, schemas, genomes, doc wiring, MVP plans, promotion,
  mutation, or retirement paths in project-infi.
---

# Subsystem Summoner Pattern (SSP)

Deterministic pipeline: raw idea seed → governed subsystem family with concept spec, schema, CISIV admission, doc tree wiring, proof posture, activation order, MVP plan, and subsystem genome (Alt-4).

Canonical protocol: [docs/contracts/AAIS_SSP_PROTOCOL.md](../../docs/contracts/AAIS_SSP_PROTOCOL.md)

**Naming (required):** [docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../../docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md) — read before Step 1. Mythic in comments; engineering in code; no new `*_organ` / `*_fabric` file stems.

Alt-4 lifecycle: [AAIS_SSP_PROMOTION_PROTOCOL.md](../../docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md), [AAIS_SUBSYSTEM_GENOME.md](../../docs/contracts/AAIS_SUBSYSTEM_GENOME.md), [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](../../docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md), [AAIS_SUBSYSTEM_MUTATION_PATH.md](../../docs/contracts/AAIS_SUBSYSTEM_MUTATION_PATH.md)

Golden examples: [examples/README.md](./examples/README.md)

## Trigger Phrases

- "Summon N subsystem families: …"
- "Run SSP on …"
- "Admit concept …"

## Input

N idea seeds — short descriptions such as:

- "Operator lineage graph"
- "Triangulation ledger"
- "Narrative trust pack"

Optional: dependency hints, target subsystem README, proof subdirectory.

## Governance Rules

**No ghost subsystems.** A subsystem is not real until it has ALL of:

1. Concept spec (`docs/_future/ideas_pending/<NAME>.md`)
2. Schema (`schemas/<name>.v1.json` + concept-origin copy)
3. Proof posture table (§8 in concept spec; claims default `none_yet`)
4. MVP plan (`docs/_future/ideas_pending/<NAME>_MVP_PLAN.md`)
5. Doc tree wiring (indexes + audit entry)
6. Subsystem genome (`governance/subsystem_genomes/<gene>.genome.v1.json`)

**Proof posture at concept:** Use `none_yet` for unproven claims. Use `asserted` only for schema-coverage claims backed by the spec + schema. Do not introduce `asserted_none_yet` as a label — that maps to `none_yet`.

**Activation rule:** Subsystems move `concept → prototype → mvp → governed` per [AAIS_SSP_PROMOTION_PROTOCOL.md](../../docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md).

**Retirement / mutation:** [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](../../docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md), [AAIS_SUBSYSTEM_MUTATION_PATH.md](../../docs/contracts/AAIS_SUBSYSTEM_MUTATION_PATH.md).

**Step 6 (scaffold) is optional:** Stubs only — no full logic unless asked.

---

## Seven-Step Pipeline (SSP + Alt-4)

Execute steps 1–5 and 7 for **each** idea seed. Step 6 is optional. For batches of N ideas, assign activation order after all specs are drafted; sync lineage symmetry among registered genomes.

### Step 1 — Generate Concept Spec

When the idea seed is **mythic-only**, run the translator first:

```bash
python tools/mythic_engineering_translator.py --mythic "<seed text>" --format markdown
```

Or `make translate-mythic MYTHIC='<seed text>'`. Copy **Mythic** and **Engineering** lines into concept spec §1.

**Output:** `docs/_future/ideas_pending/<UPPER_SNAKE>.md`

Use template: [templates/concept_spec.md](./templates/concept_spec.md)

**Required sections:**

| § | Title |
|---|-------|
| 1 | Purpose (Mythic + Engineering names) |
| 2 | Authority And Precedence |
| 3 | Non-Goals |
| 4 | Core contract (schema link + tables) |
| 5–7 | Domain-specific (correlation model, UI/handoff, etc.) |
| 7 or dedicated | Failsafe |
| 8 | Proof Posture (Concept) |
| 9 | CISIV Path |
| 10 | Related |
| 11 | Activation Order Notes And Minimal Invariants |

Header must include:

```markdown
CISIV stage: **concept**
Status: pending — not yet integrated into active AAIS doc tree or backed by runtime.
```

### Step 2 — Generate Schema

**Outputs:**

- Canonical: `schemas/<snake_case>.v1.json`
- Concept-origin copy: `docs/_future/ideas_pending/schemas/<snake_case>.v1.json`

Use template: [templates/schema_skeleton.json](./templates/schema_skeleton.json)

**Conventions** (match existing schemas):

- `"$schema": "https://json-schema.org/draft/2020-12/schema"`
- `"$id": "<snake_case>.v1"` (flat; use `platform.` prefix only for platform-scoped schemas)
- Required `{entity}_version: { "const": "<same as $id>" }`
- Required `claim_label: enum ["asserted", "proven", "rejected"]`
- Required `cisiv_stage: enum ["concept", "identity", "structure", "implementation", "verification"]`
- `$defs` with `additionalProperties: false` for nested objects
- Validate JSON parses cleanly

Reference: [schemas/ul_lineage_graph.v1.json](../../schemas/ul_lineage_graph.v1.json)

### Step 3 — Wire Doc Tree

Update these files **in order** for each new idea:

| File | Action |
|------|--------|
| [docs/_future/ideas_pending/README.md](../../docs/_future/ideas_pending/README.md) | Add row to **Pending Ideas** table (not promoted) |
| [docs/_future/README.md](../../docs/_future/README.md) | Confirm `ideas_pending/` pointer if new bucket needed |
| [docs/README.md](../../docs/README.md) | Update pending ideas list if indexed |
| [docs/runtime/AAIS_SUBSYSTEM_SPEC.md](../../docs/runtime/AAIS_SUBSYSTEM_SPEC.md) | Add to §9 Concept Pending table (`status: concept`) |
| Relevant subsystem README(s) | Add `## Pending Future Ideas` link — pattern from [mechanic/README.md](../../docs/subsystems/mechanic/README.md) |
| [docs/audit/LOGBOOK.md](../../docs/audit/LOGBOOK.md) | See Step 4 |

**Subsystem README pattern:**

```markdown
## Pending Future Ideas

- [Idea Title](../../_future/ideas_pending/IDEA_NAME.md)
  — one-line description (concept)
```

### Step 4 — Add Audit Entry

Append to [docs/audit/LOGBOOK.md](../../docs/audit/LOGBOOK.md) under today's date:

```markdown
## YYYY-MM-DD

### <Idea Title> — Concept Admission

- CISIV stage: `concept`
- scope: admitted <idea name> into `docs/_future/ideas_pending/` with CISIV concept spec, JSON schema, MVP plan, and proof posture table; cross-linked from active docs map
- outcome: <idea> documented as pending with recommended activation order <N of batch>; no runtime code changed
- verification note: doc-only pass; schema validated as JSON; `make ssp-gate` passes
```

For batches, use one combined entry listing all ideas and activation order.

### Step 5 — Generate MVP Plan

**Output:** `docs/_future/ideas_pending/<NAME>_MVP_PLAN.md`

Use template: [templates/mvp_plan.md](./templates/mvp_plan.md)

**Required sections:**

1. Minimal Runtime Surface (table)
2. Code Artifacts (bulleted modules, CLI, API routes)
3. Tests (pytest targets + what each proves)
4. Fixtures (paths + scenarios)
5. Gates (make target, governance script, sequence)
6. Proof Bundle (target path + claim table with `none_yet` labels)
7. Reproduction Commands (copy-pasteable bash)
8. Activation Dependencies (existing subsystems + batch order)

At concept admission, status is: `planned (not yet implemented)`.

### Step 6 — (Optional) Scaffold Code

Only when asked. Create empty or stub files:

- `src/<engineering_snake_case>.py` — **not** `*_organ.py` or `*_fabric.py`
- Header template: [templates/python_subsystem_header.py](./templates/python_subsystem_header.py)
- `tools/<name>/`
- `.github/scripts/check-<name>-governance.py` (stub)
- `tests/test_<name>.py` (stub)
- `fixtures/` as needed

Scaffold rules:

- Primary class: `<Domain><Function><Role>` (PascalCase)
- Dual-layer `# Mythic:` / `# Engineering:` on class and public functions
- File header: Responsibilities, Non-responsibilities, Invariants
- Functions: verb names only

Do **not** implement business logic unless explicitly requested.

### Step 7 — Generate Subsystem Genome (Alt-4)

**Output:** `governance/subsystem_genomes/<gene>.genome.v1.json`

Use template: [templates/genome.v1.json](./templates/genome.v1.json)

**Concept-stage requirements:**

- `identity.stage`: `concept`
- `proof.posture`: `asserted`
- `runtime.surface`: `[]` (no runtime code)
- `proof.bundles`: `[]`; use `target_bundles` for planned proof paths
- `ssp.summon_eligible`: `true` until promoted or retired
- `ssp.engineering_class`: PascalCase `<Domain><Function><Role>` (required after concept admission)
- `ssp.mythic_label`: short mythic name for operator docs (required)
- `ssp.linguistic_version`: `1.0.0` at concept; bump on MP-X linguistic changes

After Step 7: run `make naming-genome-gate` to capture linguistic snapshot.

**Before MP-LING apply** (when genome has `lineage.children`): run cascade impact report:

```bash
python tools/linguistic_cascade_report.py --gene <gene>
```

If [linguistic_cascade_policy.v1.json](../../governance/linguistic_cascade_policy.v1.json) sets `block_apply_without_cascade_ack: true`, include acknowledged child genes in the linguistic delta `cascade_ack` array.

Register in [governance/subsystem_genomes/README.md](../../governance/subsystem_genomes/README.md).

Update genome on promotion per [AAIS_SSP_PROMOTION_PROTOCOL.md](../../docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md).

---

## Activation Order Assignment (Batches)

When summoning N ideas in one pass:

1. Rank by dependency on **existing live** subsystems (fewer deps = lower order)
2. Rank by whether other **pending ideas in the batch** depend on it
3. Record in concept spec §11 and MVP plan §8
4. Summarize in LOGBOOK outcome

Example from golden batch (2026-06-02):

1. CISIV Operator Lineage Console — foundational governance visibility
2. Forensic Triangulation — reads Mechanic + Scorpion ledgers
3. Narrative Trust Pack — wraps Story Forge → Beatbox → Speakers chain

---

## Verification Checklist

After completing SSP for all seeds:

```bash
make ssp-gate
make genome-gate
```

Confirm:

- [ ] Each concept spec has Proof Posture and CISIV Path sections
- [ ] Each idea has paired `<NAME>_MVP_PLAN.md`
- [ ] Each schema exists in `schemas/` and `ideas_pending/schemas/`
- [ ] Each idea has genome at `governance/subsystem_genomes/<gene>.genome.v1.json`
- [ ] Lineage parents/children symmetric among registered genomes in batch
- [ ] LOGBOOK entry dated and formatted correctly
- [ ] No runtime code changed (unless Step 6 explicitly requested)

---

## Naming Conventions

Engineering protocol: [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../../docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md). Legacy `*_organ` paths are grandfathered only.

| Artifact | Convention | Example |
|----------|------------|---------|
| Concept spec file | `UPPER_SNAKE.md` | `FORENSIC_TRIANGULATION.md` |
| Runtime module (new) | `snake_case.py` (no organ/fabric suffix) | `runtime_plane_manager.py` |
| Primary class (new) | `<Domain><Function><Role>` | `RuntimePlaneManager` |
| MVP plan file | `<CONCEPT_SPEC>_MVP_PLAN.md` | `FORENSIC_TRIANGULATION_MVP_PLAN.md` |
| Schema file | `snake_case.v1.json` | `triangulation.v1.json` |
| Schema `$id` | `snake_case.v1` | `triangulation.v1` |
| Version field | `{entity}_version` const | `triangulation_version` |
| Genome gene | `snake_case` | `forensic_triangulation` |
| Genome file | `<gene>.genome.v1.json` | `forensic_triangulation.genome.v1.json` |

---

## Related Docs

- [AAIS_SSP_PROTOCOL.md](../../docs/contracts/AAIS_SSP_PROTOCOL.md)
- [AAIS_SSP_PROMOTION_PROTOCOL.md](../../docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md)
- [AAIS_SUBSYSTEM_GENOME.md](../../docs/contracts/AAIS_SUBSYSTEM_GENOME.md)
- [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](../../docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md)
- [AAIS_SUBSYSTEM_MUTATION_PATH.md](../../docs/contracts/AAIS_SUBSYSTEM_MUTATION_PATH.md)
- [AAIS_MODULE_GOVERNANCE_PROTOCOL.md](../../docs/contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
- [AAIS_SUBSYSTEM_SPEC.md](../../docs/runtime/AAIS_SUBSYSTEM_SPEC.md)
- [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../../docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md)
- [src/cisiv.py](../../src/cisiv.py)
