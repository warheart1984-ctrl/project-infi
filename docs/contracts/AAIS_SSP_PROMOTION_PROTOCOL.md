# AAIS SSP Promotion Protocol

Status: **active contract**

CISIV stage: **structure**

SSP Alt-4 lifecycle: formal promotion gates from concept through governed status.

Parent: [AAIS_SSP_PROTOCOL.md](./AAIS_SSP_PROTOCOL.md)

Genome enforcement: [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)

## Lifecycle Overview

```text
concept → prototype → mvp → governed
         (optional sandbox)   (constitutional layer)
```

Each promotion requires passing stage-specific gates and updating the subsystem
genome `identity.stage` and `proof.posture` fields.

| Stage | Genome `identity.stage` | Genome `proof.posture` |
|-------|-------------------------|------------------------|
| Concept | `concept` | `asserted` |
| Prototype | `prototype` | `prototype` |
| MVP | `mvp` | `mvp` |
| Governed | `governed` | `governed` |

## Stage 1 — Concept

A subsystem is **admitted** at concept when it has:

| Requirement | Artifact / gate |
|-------------|-----------------|
| Concept spec | `docs/_future/ideas_pending/<NAME>.md` |
| Schema | `schemas/<name>.v1.json` + concept-origin copy |
| MVP plan | `docs/_future/ideas_pending/<NAME>_MVP_PLAN.md` |
| Doc wiring | Indexes, subsystem READMEs, `AAIS_SUBSYSTEM_SPEC.md` §9 |
| Audit entry | `docs/audit/LOGBOOK.md` — Concept Admission |
| SSP bundle | `make ssp-gate` |
| Subsystem genome | `governance/subsystem_genomes/<gene>.genome.v1.json` at `stage: concept` |

**No runtime code allowed.** Genome `runtime.surface` MUST be empty.

Summon pipeline: [.cursor/skills/subsystem-summoner/SKILL.md](../../.cursor/skills/subsystem-summoner/SKILL.md)

## Stage 2 — Prototype

A subsystem becomes a **prototype** when:

| Requirement | Evidence |
|-------------|----------|
| Minimal runtime surface | Read-only or sandboxed (`runtime.surface[].isolated: true`) |
| Schema validation tests | pytest validates fixture instances against schema |
| One CLI or tool | At least one `kind: cli` or `kind: tool` entry |
| Prototype proof bundle | `docs/proof/<area>/<NAME>_PROTOTYPE_PROOF.md` |
| Prototype gate | `make <gene>-prototype-gate` (when defined) |
| Genome update | `identity.stage: prototype`, `proof.posture: prototype` |

Runtime is allowed but **must be isolated** — no integration with Mission Board,
Jarvis routing, or cross-subsystem writes until MVP promotion.

LOGBOOK entry: `### <Name> — Prototype Promotion` (CISIV stage `implementation`).

## Stage 3 — MVP

A subsystem becomes **MVP** when:

| Requirement | Evidence |
|-------------|----------|
| Runtime organ integrated | Modules/API/UI listed in genome `runtime.surface` |
| Tests cover invariants | pytest + governance gate |
| CLI + fixtures | Documented in active doc and MVP plan |
| Full proof bundle | `docs/proof/<area>/<NAME>_V1_PROOF.md` with claim posture |
| All gates pass | `make <gene>-gate` (or batch gate) |
| Docs promoted | Active doc under `docs/runtime/` or `docs/subsystems/` |
| Genome update | `identity.stage: mvp`, `proof.posture: mvp` |

Subsystem is **real** but not yet stable. Listed in `AAIS_SUBSYSTEM_SPEC.md` §8
(Partial Live) until governed.

LOGBOOK entry: `### <Name> — MVP Promotion` (CISIV stage `verification`).

Graduate from `ideas_pending/` per [ideas_pending/README.md](../_future/ideas_pending/README.md).

## Stage 4 — Governed

A subsystem becomes **governed** when:

| Requirement | Evidence |
|-------------|----------|
| Stable API | Versioned contract doc or OpenAPI freeze record |
| Stable schema | `schema.frozen: true` in genome; no breaking changes without mutation path |
| Stable proof posture | Majority claims `proven`; documented in proof bundle |
| Governance contract | Subsystem-specific contract under `docs/contracts/` or subsystem pack |
| Retirement path | Documented per [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md) |
| Mutation path | Documented per [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md) |
| Cross-reference | Referenced by at least one other subsystem genome `lineage.children` |

Subsystem is part of the **AAIS constitutional layer**.

LOGBOOK entry: `### <Name> — Governed Promotion` (CISIV stage `verification`).

Genome update: `identity.stage: governed`, `proof.posture: governed`.

## Promotion Checklist (Operator)

```bash
make ssp-gate
make genome-gate
# stage-specific:
make <gene>-gate          # MVP+
```

## Demotion

Demotion (MVP → prototype → concept) requires:

- LOGBOOK entry with CISIV stage `structure`
- Genome stage regression with audit rationale
- Active doc marked deprecated; runtime isolated or removed per retirement protocol

## Related

- [AAIS_SSP_PROTOCOL.md](./AAIS_SSP_PROTOCOL.md)
- [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md)
- [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md)
- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)
- [AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md)
