# SSP Golden Examples

These three subsystems completed the full SSP pipeline and graduated to partial live MVP.

| Idea | Concept spec | MVP plan | Schema | Active doc | Proof |
|------|--------------|----------|--------|------------|-------|
| CISIV Operator Lineage Console | [CISIV_OPERATOR_LINEAGE_CONSOLE.md](../../../docs/_future/ideas_pending/CISIV_OPERATOR_LINEAGE_CONSOLE.md) | [CISIV_OPERATOR_LINEAGE_CONSOLE_MVP_PLAN.md](../../../docs/_future/ideas_pending/CISIV_OPERATOR_LINEAGE_CONSOLE_MVP_PLAN.md) | [ul_lineage_graph.v1.json](../../../schemas/ul_lineage_graph.v1.json) | [UL_LINEAGE_CONSOLE.md](../../../docs/runtime/UL_LINEAGE_CONSOLE.md) | [UL_LINEAGE_CONSOLE_V1_PROOF.md](../../../docs/proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md) |
| Forensic Triangulation Ledger | [FORENSIC_TRIANGULATION.md](../../../docs/_future/ideas_pending/FORENSIC_TRIANGULATION.md) | [FORENSIC_TRIANGULATION_MVP_PLAN.md](../../../docs/_future/ideas_pending/FORENSIC_TRIANGULATION_MVP_PLAN.md) | [triangulation.v1.json](../../../triangulation/schemas/triangulation.v1.json) | [TRIANGULATION.md](../../../docs/subsystems/forensics/TRIANGULATION.md) | [TRIANGULATION_V1_PROOF.md](../../../docs/proof/forensics/TRIANGULATION_V1_PROOF.md) |
| Narrative Trust Pack | [NARRATIVE_TRUST_PACK.md](../../../docs/_future/ideas_pending/NARRATIVE_TRUST_PACK.md) | [NARRATIVE_TRUST_PACK_MVP_PLAN.md](../../../docs/_future/ideas_pending/NARRATIVE_TRUST_PACK_MVP_PLAN.md) | [narrative_trust_pack.v1.json](../../../schemas/narrative_trust_pack.v1.json) | [NARRATIVE_TRUST_PACK.md](../../../docs/subsystems/storyforge/NARRATIVE_TRUST_PACK.md) | [NARRATIVE_TRUST_PACK_V1_PROOF.md](../../../docs/proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md) |

Use these as reference when summoning new subsystem families.

## Engineering scaffold example (new admissions)

For a seed "Runtime plane steward", SSP Step 6 would scaffold:

| Field | Value |
|-------|-------|
| Mythic | Runtime plane steward |
| Engineering class | `RuntimePlaneManager` |
| Module | `src/runtime_plane_manager.py` |
| Function | `synchronize_runtime_planes()` |

Template: [../templates/python_subsystem_header.py](../templates/python_subsystem_header.py). Do not use `runtime_plane_organ.py`.
