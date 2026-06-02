# Recipe Module — MVP Plan

CISIV stage: concept → implementation target

Status: **implemented (partial live)** — see [../../subsystems/platform/RECIPE_MODULE.md](../../subsystems/platform/RECIPE_MODULE.md)

Concept origin: [./RECIPE_MODULE.md](./RECIPE_MODULE.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| Pack store | `src/recipe_module.py` | Load/validate recipe_module.v1.json |
| Persistence | `.runtime/recipe_module/<recipe_id>/` | Schema-validated packs + ledger |
| API | `POST /api/missions/from-recipe` | Draft mission from pack |
| Schema | `schemas/recipe_module.v1.json` | Canonical |
| Gate | `make recipe-module-gate` | Governance + fixture replay |

## 2. Code Artifacts

- `src/recipe_module.py` — pack loader, step runner, gate evaluator
- `src/api.py` — recipe admission route (distinct from preset endpoint)
- `tools/recipe/` — fixture packs and CLI inspect helper
- `.github/scripts/check-recipe-module-governance.py` — governance gate

## 3. Tests

- `tests/test_recipe_module.py` — schema validation, gate halt on failure, signoff_required enforcement, no conflation with preset recipes

## 4. Fixtures

- `tools/recipe/fixtures/onboarding-v1.json` — three-step demo with human_signoff gate

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make recipe-module-gate` | `.github/scripts/check-recipe-module-governance.py` | pytest → validate fixture pack → assert ledger append |

## 6. Proof Bundle

Target: [../../proof/platform/RECIPE_MODULE_V1_PROOF.md](../../proof/platform/RECIPE_MODULE_V1_PROOF.md)

| Claim | Label | Evidence |
|-------|-------|----------|
| Fixture pack validates against schema | `none_yet` | Requires implementation |
| Mission draft created from recipe without bypassing signoff | `none_yet` | Requires implementation |
| API preset recipes documented as separate surface | `none_yet` | Requires verification |

## 7. Reproduction Commands

```bash
make recipe-module-gate
python -m pytest tests/test_recipe_module.py -q
python -m tools.recipe.inspect --recipe-id onboarding-v1
```

## 8. Activation Dependencies

**Existing subsystems required:** Mission Board, Platform membrane, CISIV/UL step envelopes

**Order among batch:** 1 of 3 (most foundational — workflow templates before creative/voice lanes)

**Rationale:** Recipe Module governs repeatable operator workflows with fewest dependencies on other pending ideas in this batch. Imagine Generator and Human Voice Extraction may consume recipe-shaped handoffs later but do not block Recipe admission.
