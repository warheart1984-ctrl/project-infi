# Imagine Generator — MVP Plan

CISIV stage: concept → implementation target

Status: **implemented (partial live)** — see [../../subsystems/storyforge/IMAGINE_GENERATOR.md](../../subsystems/storyforge/IMAGINE_GENERATOR.md)

Concept origin: [./IMAGINE_GENERATOR.md](./IMAGINE_GENERATOR.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| Emitter | `src/imagine_generator.py` | Pattern emit + constraint check |
| Persistence | `.runtime/imagine_generator/<pattern_id>/` | Schema-validated artifacts |
| Bridge | `src/capabilities/imagine_generator.py` | Jarvis-governed capability route |
| Schema | `schemas/imagine_generator.v1.json` | Canonical |
| Gate | `make imagine-generator-gate` | Governance + fixture handoff |

## 2. Code Artifacts

- `src/imagine_generator.py` — pattern builder, constraint evaluator, ledger append
- `src/capabilities/imagine_generator.py` — capability bridge adapter
- `tools/imagine/` — fixture patterns and inspect CLI
- `.github/scripts/check-imagine-generator-governance.py` — governance gate

## 3. Tests

- `tests/test_imagine_generator.py` — schema validation, constraint rejection, Story Forge handoff stub, no sovereign subsystem routing

## 4. Fixtures

- `tools/imagine/fixtures/scene-seed-demo.json` — scene_seed with tone + forbidden_term constraints

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make imagine-generator-gate` | `.github/scripts/check-imagine-generator-governance.py` | pytest → validate fixture → assert handoff record |

## 6. Proof Bundle

Target: [../../proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md](../../proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md)

| Claim | Label | Evidence |
|-------|-------|----------|
| Fixture pattern validates against schema | `none_yet` | Requires implementation |
| Story Forge admits pattern without bypassing canonical lane | `none_yet` | Requires implementation |
| Adapter lineage documented separately from governed contract | `none_yet` | Requires verification |

## 7. Reproduction Commands

```bash
make imagine-generator-gate
python -m pytest tests/test_imagine_generator.py -q
python -m tools.imagine.inspect --pattern-id scene-seed-demo
```

## 8. Activation Dependencies

**Existing subsystems required:** Story Forge (partial live), capability service bridge, Jarvis authority

**Order among batch:** 2 of 3 — after Recipe Module; before Human Voice Extraction

**Rationale:** Imagine Generator wraps creative pattern emission for Story Forge handoff. It does not require Human Voice profiles. Recipe Module may supply repeatable workflow shells that include imagine steps, but Imagine does not block on Recipe promotion.
