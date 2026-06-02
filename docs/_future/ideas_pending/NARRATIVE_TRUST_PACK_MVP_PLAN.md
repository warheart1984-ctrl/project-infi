# Narrative Trust Pack — MVP Plan

CISIV stage: concept → implementation target

Status: **implemented (partial live)** — see [../../subsystems/storyforge/NARRATIVE_TRUST_PACK.md](../../subsystems/storyforge/NARRATIVE_TRUST_PACK.md)

Concept origin: [./NARRATIVE_TRUST_PACK.md](./NARRATIVE_TRUST_PACK.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| Wrapper | `src/capabilities/narrative_trust_pack.py` | Pack builder + hash verification |
| CLI | `python -m tools.narrative pack\|verify\|signoff` | Operator entry |
| Output | `.runtime/narrative/<pack_id>/narrative_trust_pack.v1.json` | Governed export |
| Schema | `schemas/narrative_trust_pack.v1.json` | Three-stage chain |

## 2. Code Artifacts

- `src/capabilities/narrative_trust_pack.py` — pack builder, signoff gate, tamper detection
- `tools/narrative/__main__.py` — CLI (`pack`, `verify`, `signoff`)
- `.github/scripts/check-narrative-governance.py` — governance gate

## 3. Tests

- `tests/test_narrative_trust_pack.py` — E2E pack build, signoff promotion to `proven`, tampered artifact rejection

## 4. Fixtures

- Inline test fixtures in `tests/test_narrative_trust_pack.py` — story_forge_audio output stubs for three-stage chain

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make narrative-gate` | `.github/scripts/check-narrative-governance.py` | pytest only |

## 6. Proof Bundle

Target: [../../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md](../../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md)

| Claim | Label | Evidence |
|-------|-------|----------|
| E2E pack + signoff → proven | `proven` | `tests/test_narrative_trust_pack.py` |
| Tampered artifact → rejected | `proven` | Tamper test in pytest |
| Jarvis capability route | `none_yet` | Deferred registration |

## 7. Reproduction Commands

```bash
make narrative-gate
python -m pytest tests/test_narrative_trust_pack.py -q
```

## 8. Activation Dependencies

**Existing subsystems required:** Story Forge audio adapter, Beatbox adapter, Speakers downstream lane, SignoffPolicy pattern from AI Slingshot

**Order among batch:** 3 of 3 — depends on creative pipeline adapters being callable

**Rationale:** NTP wraps existing Story Forge → Beatbox → Speakers outputs; it does not create a sovereign creative subsystem. Activates last because it depends on the media chain adapters and human signoff infrastructure.
