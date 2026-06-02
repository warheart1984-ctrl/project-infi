# Human Voice Extraction

Status: **partial live** — extract, signoff, Speakers constraints handoff MVP.

CISIV stage: **implementation** (proof: `docs/proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md`)

## Runtime

| Surface | Location |
|---------|----------|
| Core | `src/human_voice_extraction.py` |
| Capability | `src/capabilities/human_voice_extraction.py` |
| API | `POST /api/jarvis/human-voice/extract`, `/signoff`, `/handoff` |
| Capability bridge | `human_voice_extraction` / `extract`, `signoff`, `handoff` |
| Fixture | `tools/human_voice/fixtures/notes-demo-redacted.json` |
| Constraints | `.runtime/speakers/voice_constraints/<profile_id>.json` |
| Gate | `make human-voice-extraction-gate` |

## Verification

```bash
make human-voice-extraction-gate
python -m pytest tests/test_human_voice_extraction.py tests/test_capability_bridge_alt3.py tests/test_alt3_lineage.py -q
```

## Related

- Concept: [../../_future/ideas_pending/HUMAN_VOICE_EXTRACTION.md](../../_future/ideas_pending/HUMAN_VOICE_EXTRACTION.md)
- Proof: [../../proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md](../../proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md)
