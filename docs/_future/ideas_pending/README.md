# Ideas Pending

This folder holds future ideas documented at **CISIV concept stage** but not yet
integrated into the active AAIS doc tree or backed by runtime.

Nothing here is live system truth unless promoted per the rule below.

SSP governs new admissions — see [../../contracts/AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md).

## Promoted to Partial Live (MVP)

These ideas now have runtime MVP + proof packets — see active docs:

| Idea | Active doc | MVP plan | Proof |
|------|------------|----------|-------|
| CISIV Operator Lineage Console | [../../runtime/UL_LINEAGE_CONSOLE.md](../../runtime/UL_LINEAGE_CONSOLE.md) | [CISIV_OPERATOR_LINEAGE_CONSOLE_MVP_PLAN.md](./CISIV_OPERATOR_LINEAGE_CONSOLE_MVP_PLAN.md) | [../../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md](../../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md) |
| Forensic Triangulation Ledger | [../../subsystems/forensics/TRIANGULATION.md](../../subsystems/forensics/TRIANGULATION.md) | [FORENSIC_TRIANGULATION_MVP_PLAN.md](./FORENSIC_TRIANGULATION_MVP_PLAN.md) | [../../proof/forensics/TRIANGULATION_V1_PROOF.md](../../proof/forensics/TRIANGULATION_V1_PROOF.md) |
| Narrative Trust Pack (NTP) | [../../subsystems/storyforge/NARRATIVE_TRUST_PACK.md](../../subsystems/storyforge/NARRATIVE_TRUST_PACK.md) | [NARRATIVE_TRUST_PACK_MVP_PLAN.md](./NARRATIVE_TRUST_PACK_MVP_PLAN.md) | [../../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md](../../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md) |

Concept-origin specs (historical):

- [FORENSIC_TRIANGULATION.md](./FORENSIC_TRIANGULATION.md)
- [CISIV_OPERATOR_LINEAGE_CONSOLE.md](./CISIV_OPERATOR_LINEAGE_CONSOLE.md)
- [NARRATIVE_TRUST_PACK.md](./NARRATIVE_TRUST_PACK.md)

## Pending Ideas (Concept)

| Idea | Concept spec | MVP plan | Schema |
|------|--------------|----------|--------|
| *(none)* | — | — | — |

## Promotion Rule

An idea graduates from pending when:

1. Its spec is admitted into `docs/subsystems/` or `docs/runtime/` (or contracts)
2. Runtime code backs the claimed behavior
3. A proof packet exists under `docs/proof/` with appropriate claim labels

Full SSP bundle required at concept admission: concept spec + schema + MVP plan + proof posture + doc wiring.

## Schemas

- [schemas/triangulation.v1.json](./schemas/triangulation.v1.json)
- [schemas/ul_lineage_graph.v1.json](./schemas/ul_lineage_graph.v1.json)
- [schemas/narrative_trust_pack.v1.json](./schemas/narrative_trust_pack.v1.json)

Runtime copies also live under `schemas/`, `triangulation/schemas/`.

## SSP Gate

```bash
make ssp-gate
```
