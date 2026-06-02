# Imagine Generator

Status: **partial live** — pattern emit + Story Forge admission handoff + optional Grok render MVP.

CISIV stage: **implementation** (proof: `docs/proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md`)

## Runtime

| Surface | Location |
|---------|----------|
| Core | `src/imagine_generator.py` |
| Grok adapter | `src/imagine_grok.py` (env keys only) |
| Capability | `src/capabilities/imagine_generator.py` |
| Capability bridge | `imagine_generator` / `emit`, `handoff`, `grok_render` |
| API | `POST /api/jarvis/imagine/emit`, `/handoff`, `/grok-render` |
| Keys status | `GET /api/jarvis/imagine/keys-status` |
| Fixture | `tools/imagine/fixtures/scene-seed-demo.json` |
| Admissions | `.runtime/story_forge/imagine_admissions/<pattern_id>.json` |
| Grok artifact | `.runtime/imagine_generator/<pattern_id>/grok_render.json` |
| Gate | `make imagine-generator-gate` |

## xAI API keys (required for Grok render)

Grok render **does not run** unless one of these environment variables is set (no per-request keys, no persistence):

```text
STORY_FORGE_XAI_API_KEY   (preferred)
XAI_API_KEY               (fallback)
```

Check configuration without exposing secrets:

```bash
curl http://localhost:5000/api/jarvis/imagine/keys-status
```

Capability bridge action `grok_render` and `POST /api/jarvis/imagine/grok-render` return `keys_required` (HTTP 428 on API) when unset.

## Verification

```bash
make imagine-generator-gate
python -m pytest tests/test_imagine_generator.py tests/test_imagine_grok.py -q
```

## Related

- Concept: [../../_future/ideas_pending/IMAGINE_GENERATOR.md](../../_future/ideas_pending/IMAGINE_GENERATOR.md)
- Proof: [../../proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md](../../proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md)
