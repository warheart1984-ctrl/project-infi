# Narrative Trust Pack (NTP)

Status: **partial live** — pack builder + CLI + Jarvis bridge/API.

CISIV stage: **implementation** (verification proof: `docs/proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md`)

## Purpose

Governed export wrapper for Story Forge → Beatbox → Speakers pipeline stages with hash verification and human signoff before `proven` export.

## Runtime

| Surface | Location |
|---------|----------|
| Wrapper | `src/capabilities/narrative_trust_pack.py` |
| CLI | `python -m tools.narrative pack\|verify\|signoff` |
| API | `POST /api/jarvis/narrative/pack`, `/verify`, `/signoff` |
| Bridge | `narrative_trust_pack` / `pack`, `verify`, `signoff` |
| Output | `.runtime/narrative/<pack_id>/narrative_trust_pack.v1.json` |
| Schema | `schemas/narrative_trust_pack.v1.json` |
| Gate | `make narrative-gate` |

## Verification

```bash
make narrative-gate
python -m pytest tests/test_narrative_trust_pack.py tests/test_capability_bridge_alt3.py -q
```

## Related

- Concept origin: [../../_future/ideas_pending/NARRATIVE_TRUST_PACK.md](../../_future/ideas_pending/NARRATIVE_TRUST_PACK.md)
- Proof: [../../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md](../../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md)
- Story Forge chain: [STORYFORGE_STAGE_SPEC.md](./STORYFORGE_STAGE_SPEC.md)
