# Human Voice Extraction — MVP Plan

CISIV stage: concept → implementation target

Status: **implemented (partial live)** — see [../../subsystems/speakers/HUMAN_VOICE_EXTRACTION.md](../../subsystems/speakers/HUMAN_VOICE_EXTRACTION.md)

Concept origin: [./HUMAN_VOICE_EXTRACTION.md](./HUMAN_VOICE_EXTRACTION.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| Extractor | `src/human_voice_extraction.py` | Profile emit + redaction |
| Persistence | `.runtime/human_voice_extraction/<extraction_id>/` | Schema-validated packs |
| Bridge | `src/capabilities/human_voice_extraction.py` | Jarvis-governed route |
| Speakers hook | `external/beatbox_speakers/` adapter boundary | Handoff constraints only |
| Schema | `schemas/human_voice_extraction.v1.json` | Canonical |
| Gate | `make human-voice-extraction-gate` | Governance + retention checks |

## 2. Code Artifacts

- `src/human_voice_extraction.py` — extraction, trait normalization, retention enforcement
- `src/capabilities/human_voice_extraction.py` — capability bridge adapter
- `tools/human_voice/` — fixture notes (synthetic) and inspect CLI
- `.github/scripts/check-human-voice-extraction-governance.py` — governance gate

## 3. Tests

- `tests/test_human_voice_extraction.py` — schema validation, `store_raw_source: false` enforcement, signoff-gated handoff, redaction before proven label

## 4. Fixtures

- `tools/human_voice/fixtures/notes-demo-redacted.json` — synthetic human_notes source with expected trait output

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make human-voice-extraction-gate` | `.github/scripts/check-human-voice-extraction-governance.py` | pytest → validate fixture → assert no raw source persistence |

## 6. Proof Bundle

Target: [../../proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md](../../proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md)

| Claim | Label | Evidence |
|-------|-------|----------|
| Fixture extraction validates; raw source not stored | `none_yet` | Requires implementation |
| Speakers handoff blocked without signoff | `none_yet` | Requires implementation |
| Lumen docs not conflated with this family | `none_yet` | Requires verification |

## 7. Reproduction Commands

```bash
make human-voice-extraction-gate
python -m pytest tests/test_human_voice_extraction.py -q
python -m tools.human_voice.inspect --extraction-id notes-demo-redacted
```

## 8. Activation Dependencies

**Existing subsystems required:** Speakers (partial live), Nova/Jarvis authority, Beatbox upstream timing (read-only for handoff order)

**Order among batch:** 3 of 3 (last — highest privacy/safety bar; depends on voice lane semantics)

**Rationale:** Human Voice Extraction governs sensitive profile material for Speakers. It should activate after Recipe Module (workflows) and Imagine Generator (creative patterns) because operators benefit from stable workflow and creative lanes before voice-profile admission, and because retention/signoff rules are the strictest in this batch.
