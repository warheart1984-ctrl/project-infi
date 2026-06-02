# Recipe Module

Status: **partial live** — governed recipe packs + Mission Board admission MVP.

CISIV stage: **implementation** (verification proof: `docs/proof/platform/RECIPE_MODULE_V1_PROOF.md`)

## Purpose

Versioned workflow recipe packs (steps, inputs, gates) admissible to Mission Board. Distinct from built-in `MISSION_PRESETS` / `from-preset` API.

## Runtime

| Surface | Location |
|---------|----------|
| Core | `src/recipe_module.py` |
| Mission admission | `mission_board.create_from_recipe` |
| API | `POST /api/jarvis/missions/from-recipe` |
| Capability bridge | `recipe_module` / `create_mission` |
| Fixture | `tools/recipe/fixtures/onboarding-v1.json` |
| Persistence | `.runtime/recipe_module/<recipe_id>/` |
| Gate | `make recipe-module-gate` |

## Verification

```bash
make recipe-module-gate
python -m pytest tests/test_recipe_module.py tests/test_capability_bridge_alt3.py tests/test_alt3_lineage.py -q
python -m tools.recipe --recipe-id onboarding-v1 --signoff-ack
```

## Related

- Concept origin: [../../_future/ideas_pending/RECIPE_MODULE.md](../../_future/ideas_pending/RECIPE_MODULE.md)
- Proof: [../../proof/platform/RECIPE_MODULE_V1_PROOF.md](../../proof/platform/RECIPE_MODULE_V1_PROOF.md)
