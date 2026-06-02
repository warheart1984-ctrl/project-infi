# Recipe Module

CISIV stage: **implementation** (MVP live — see [../../subsystems/platform/RECIPE_MODULE.md](../../subsystems/platform/RECIPE_MODULE.md))

Status: partial live — recipe packs + Mission Board from-recipe API. Proof: [../../proof/platform/RECIPE_MODULE_V1_PROOF.md](../../proof/platform/RECIPE_MODULE_V1_PROOF.md)

## 1. Purpose

Provide **versioned, governed recipe packs** — ordered steps, typed inputs, and
admission gates — that operators can attach to Mission Board workflows without
inventing ad-hoc scripts per mission.

Archive corpus material (`Recipe module (1).docx`, `recipemodule.docx`) describes
repeatable operator workflows; this concept admits that family into AAIS law as a
schema-backed artifact, not as chat folklore.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Recipe Module sits under Mission Board and Jarvis authority. Recipes **propose**
missions and steps; they do not auto-apply repo mutations or bypass human signoff.

## 3. Non-Goals

- Not a rename or replacement of built-in **mission preset** endpoints in
  `src/api.py` (`test_mission_board_preset_endpoint_creates_recipe`) — those remain
  API convenience until this subsystem is promoted
- No auto-apply without explicit signoff gate (`signoff_required` default true)
- No sovereign subsystem front door — admission via Mission Board / Platform membrane
- No embedding of secrets or credentials inside recipe packs

## 4. Recipe Pack Contract

Schema: [schemas/recipe_module.v1.json](./schemas/recipe_module.v1.json)

| Field | Role |
|-------|------|
| `recipe_module_version` | Must be `recipe_module.v1` |
| `recipe_id` | Stable pack identifier |
| `recipe_name` | Operator-facing label |
| `steps` | Ordered actions with per-step `claim_label` |
| `inputs` | Typed mission/session/artifact inputs |
| `gates` | `human_signoff`, `schema_valid`, `make_target`, `cisiv_stage_min` |
| `signoff_required` | Default true — blocks silent promotion |
| `cisiv_stage` | Pack-level CISIV summary |
| `claim_label` | Overall pack posture |

Runtime layout (proposed):

```text
.runtime/recipe_module/<recipe_id>/
  recipe_module.v1.json
  execution_ledger.jsonl
```

## 5. Mission Board Handoff

Recipes may reference `mission_template_id` to seed Mission Board state:

- Operator selects a recipe pack → system validates schema → emits mission draft
- Each step execution appends to `execution_ledger.jsonl` with CISIV stage at emit time
- Failed gate → step remains `asserted` or `rejected`; no downstream auto-run

Structured tool envelope (future):

```json
{
  "tool": "recipe_module",
  "recipe_id": "onboarding-v1",
  "mission_id": "mission-abc-001"
}
```

## 6. Gate Model

| Gate type | Behavior |
|-----------|----------|
| `human_signoff` | Operator must acknowledge before next step |
| `schema_valid` | Target artifact must validate named schema |
| `make_target` | Named make gate must pass (e.g. `ssp-gate`) |
| `cisiv_stage_min` | Emitted envelopes must meet minimum CISIV stage |

## 7. Failsafe

- Unknown `recipe_id` → reject with explicit error; no partial mission creation
- Missing required input → halt at step boundary with `claim_label: asserted`
- Gate failure → do not advance `step_order`; surface gate id in ledger
- Conflicting `claim_label` on steps → surface all; do not auto-resolve

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers steps, inputs, gates, and version const | `asserted` | Schema + this document |
| Fixture recipe executes through Mission Board handoff | `none_yet` | Requires implementation |
| `make recipe-module-gate` passes on demo pack | `none_yet` | Requires structure stage |
| Distinct from API mission presets documented in tests | `none_yet` | Requires implementation + audit note |

Target proof packet: `docs/proof/platform/RECIPE_MODULE_V1_PROOF.md` (not yet created).

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Identity | `recipe_id` tied to Mission Board keys |
| Structure | `src/recipe_module.py` + governance gate |
| Implementation | API route + operator recipe picker |
| Verification | Fixture replay with proven step chain |

## 10. Related

- [../../runtime/AAIS_SUBSYSTEM_SPEC.md](../../runtime/AAIS_SUBSYSTEM_SPEC.md)
- [../../audit/DOCUMENT_CORPUS_SUBSYSTEM_AUDIT.md](../../audit/DOCUMENT_CORPUS_SUBSYSTEM_AUDIT.md) (Recipe Module — archive_only_high_signal)
- [../../../src/mission_board.py](../../../src/mission_board.py)
- Archive: `docs/_archive/workspace_pull/project-infi-root/Recipe module (1).docx`, `recipemodule.docx`

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** 1 of 3 — activate first

**Depends on:** Mission Board, Platform membrane ingress, CISIV/UL substrate for step envelopes

**Minimal invariants:**

- Recipe packs do not auto-apply without passing configured gates
- Built-in API mission presets remain separate until explicit migration
- No repo mutation without human signoff when `signoff_required` is true
- Unknown recipe or missing input → hard stop at step boundary
