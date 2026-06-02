# Human Voice Extraction

CISIV stage: **implementation** (MVP live — see [../../subsystems/speakers/HUMAN_VOICE_EXTRACTION.md](../../subsystems/speakers/HUMAN_VOICE_EXTRACTION.md))

Status: partial live — extract, signoff, Speakers constraints handoff. Proof: [../../proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md](../../proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md)

## 1. Purpose

Extract **governed voice-profile constraints** from human notes, operator
transcripts, or referenced voice samples — producing schema-backed traits for
Speakers downstream lanes without retaining raw PII beyond policy.

Archive corpus material (`human_notes_extraction.docx`, `Jon Halstead - Human Voice
Extracted.docx`) describes human voice capture from notes; this concept admits that
family under Jarvis/Nova authority with explicit retention rules, distinct from
the separate Lumen embodiment archive family.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Human Voice Extraction is **subordinate to Jarvis and Nova**. Extraction proposes
profiles; Speakers owns mix/render handoff truth. No bypass of signoff for
`speakers_handoff.handoff_ready: true`.

## 3. Non-Goals

- No raw PII retention when `retention_policy.store_raw_source` is false (schema const)
- No bypass of Jarvis/Nova authority for voice-bearing capabilities
- No merge with Lumen embodiment / voice doctrine archive (separate family per corpus audit)
- Not a sovereign subsystem — admission via Speakers + Nova cross-links only
- No automatic Speakers render without operator signoff when handoff requires it
- Not replacing Beatbox timing/score authority

## 4. Extraction Artifact Contract

Schema: [schemas/human_voice_extraction.v1.json](./schemas/human_voice_extraction.v1.json)

| Field | Role |
|-------|------|
| `human_voice_extraction_version` | Must be `human_voice_extraction.v1` |
| `extraction_id` | Stable extraction run identifier |
| `source_kind` | `human_notes`, `voice_sample_ref`, `operator_transcript` |
| `content_hash` | Hash of redacted/normalized source material |
| `voice_profile` | Trait bundle (pace, register, vocabulary, etc.) |
| `retention_policy` | `store_raw_source: false` required; `ttl_hours` bound |
| `speakers_handoff` | Handoff readiness + optional signoff |
| `cisiv_stage` | Extraction-level CISIV summary |
| `claim_label` | Overall extraction posture |

Runtime layout (proposed):

```text
.runtime/human_voice_extraction/<extraction_id>/
  human_voice_extraction.v1.json
  extraction_ledger.jsonl
```

## 5. Speakers And Nova Handoff

Voice profiles feed Speakers as **constraints**, not as final audio truth:

- Nova may initiate extraction requests; Jarvis must authorize capability emission
- `speakers_handoff.handoff_ready` requires signoff fields when promoting to mix lane
- Beatbox remains upstream of Speakers for timing/score; extraction does not replace it

Structured capability envelope (future):

```json
{
  "capability": "human_voice_extraction",
  "source_kind": "human_notes",
  "mission_id": "mission-abc-001"
}
```

## 6. Retention And Redaction Model

| Rule | Enforcement |
|------|-------------|
| `store_raw_source` | Schema const `false` at concept — raw notes not persisted in pack |
| `ttl_hours` | Profile traits expire; re-extraction required after TTL |
| `redaction_applied` | Must be true before `claim_label` may move toward `proven` |
| `content_hash` | Binds to redacted normalized source only |

## 7. Failsafe

- Retention policy violation → reject pack; `claim_label: rejected`
- Missing traits after extraction → `asserted` partial; no Speakers handoff
- Handoff without signoff when required → block `handoff_ready`
- PII detected in trait values → redact or reject; never silent store

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema enforces `store_raw_source: false` and trait model | `asserted` | Schema + this document |
| Fixture extraction produces Speakers-ready profile | `none_yet` | Requires implementation |
| `make human-voice-extraction-gate` passes on demo extraction | `none_yet` | Requires structure stage |
| Lumen archive explicitly out of scope | `none_yet` | Requires doc cross-check in proof packet |

Target proof packet: `docs/proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md` (not yet created).

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Identity | `extraction_id` tied to mission/session; content_hash contract |
| Structure | `src/human_voice_extraction.py` + redaction helper |
| Implementation | Capability route + Speakers admit hook |
| Verification | Fixture extraction with proven handoff under retention rules |

## 10. Related

- [../../subsystems/speakers/SPEAKERS_CANONICAL.md](../../subsystems/speakers/SPEAKERS_CANONICAL.md)
- [../../subsystems/nova/TINY_NOVA_CANONICAL.md](../../subsystems/nova/TINY_NOVA_CANONICAL.md)
- [../../subsystems/beatbox/README.md](../../subsystems/beatbox/README.md)
- [../../audit/DOCUMENT_CORPUS_SUBSYSTEM_AUDIT.md](../../audit/DOCUMENT_CORPUS_SUBSYSTEM_AUDIT.md) (Human Notes / Voice Extraction — archive_only_high_signal)
- Archive: `docs/_archive/workspace_pull/project-infi-root/human_notes_extraction.docx`, `Jon Halstead - Human Voice Extracted.docx`

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** 3 of 3 — activate last

**Depends on:** Speakers (partial live), Nova/Jarvis authority, optional Imagine Generator patterns for creative context (not required for v1 extraction)

**Minimal invariants:**

- `retention_policy.store_raw_source` remains false for v1 concept
- No Speakers handoff without signoff when handoff requires it
- Jarvis authorizes extraction capability calls
- Lumen embodiment remains a separate archive-only family
