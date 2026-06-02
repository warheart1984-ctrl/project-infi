# Narrative Trust Pack (NTP)

CISIV stage: **implementation** (MVP live — see [../../subsystems/storyforge/NARRATIVE_TRUST_PACK.md](../../subsystems/storyforge/NARRATIVE_TRUST_PACK.md))

Status: partial live — pack builder + CLI. Proof: [../../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md](../../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md)

## 1. Purpose

Apply constitutional proof posture to the **Story Forge → Beatbox → Speakers**
media chain. Creative outputs today lack the UL + law envelope that chat replies
and repo mutations receive.

NTP wraps each pipeline stage artifact in claim-labeled UL envelopes and exports
a governed bundle before any release-ready "movie package" ships.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

NTP is subordinate to Jarvis capability routing. It does not create a sovereign
creative subsystem or bypass Project Infi law on repo paths.

## 3. Non-Goals

- No Text-to-3D, Bloodrose, Lumen, or archive-family wholesale revival
- No new model zoo or standalone creative front door
- No auto-publish without human signoff on `proven` exports
- No bypass of existing Story Forge / Beatbox / Speakers adapters

## 4. Pipeline Stages

| Stage | Adapter | Default claim |
|-------|---------|---------------|
| Story Forge | `src/capabilities/story_forge_audio.py`, `external/story_forge/` | `asserted` |
| Beatbox | `external/ai/beatbox/adapter.py` | `asserted` |
| Speakers | Speakers downstream lane | `asserted` |

Each stage emits a **stage envelope**:

- `stage_id`, `stage_name`, `artifact_hash`, `ul_substrate` (subset)
- `claim_label`, `author`, `created_at_utc`

## 5. Pack Contract

Schema: [schemas/narrative_trust_pack.v1.json](./schemas/narrative_trust_pack.v1.json)

Root object `narrative_trust_pack.v1`:

| Field | Role |
|-------|------|
| `pack_id` | Unique pack identifier |
| `session_id` | Originating Jarvis session (optional) |
| `stages` | Ordered stage envelopes |
| `signoff` | Human signoff record (required for `proven`) |
| `claim_label` | Pack-level posture |
| `export_ready` | `true` only when `claim_label: proven` |

Runtime layout (proposed):

```text
.runtime/narrative/<pack_id>/
  narrative_trust_pack.v1.json
  stages/
    story_forge/
    beatbox/
    speakers/
```

## 6. Human Signoff Gate

Reuse the `SignoffPolicy` pattern from AI Slingshot
(`mechanic/hosted/models.py`):

- Operator MUST explicitly sign off before pack `claim_label` advances to `proven`
- Tampered intermediate artifact (hash mismatch) → block signoff; emit `rejected`
- Signoff record includes `signoff_by`, `signoff_at_utc`, `override_command`

## 7. Operator Entry (Future)

Via existing Jarvis capability route — not a new subsystem front door:

```json
{
  "capability": "narrative_trust_pack",
  "session_id": "<session_id>",
  "stages": ["story_forge", "beatbox", "speakers"]
}
```

CLI (implementation stage):

```bash
python -m tools.narrative pack --session-id <session_id>
```

## 8. Failsafe

- Missing stage artifact → partial pack with `claim_label: asserted`; `export_ready: false`
- Signoff without all stage hashes verified → reject with explicit reason
- Drift on any stage envelope → block `proven` promotion

## 9. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers three-stage audio chain | `asserted` | Schema + this document |
| End-to-end fixture produces `proven` pack after signoff | `none_yet` | Requires implementation |
| Drift test detects tampered intermediate artifact | `none_yet` | Requires structure stage |
| Jarvis capability wrapper composes existing adapters | `none_yet` | Requires implementation |

Target proof packet: `docs/proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md`
(not yet created).

## 10. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema |
| Identity | Pack ID, stage artifact hashes, signoff records |
| Structure | `src/capabilities/narrative_trust_pack.py` wrapper |
| Implementation | CLI + optional UI download |
| Verification | E2E fixture + tamper drift test |

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** 3 of 3 — after Lineage Console and Triangulation

**Depends on:** Story Forge audio adapter, Beatbox adapter, Speakers downstream lane, SignoffPolicy pattern from AI Slingshot

**Minimal invariants:**

- NTP is subordinate to Jarvis capability routing; no sovereign creative subsystem
- `export_ready: true` only when `claim_label: proven` and human signoff recorded
- Tampered intermediate artifact (hash mismatch) → block signoff; emit `rejected`
- Missing stage artifact → partial pack with `claim_label: asserted`; `export_ready: false`
- No auto-publish without human signoff on `proven` exports

## 12. Related

- [../../subsystems/storyforge/README.md](../../subsystems/storyforge/README.md)
- [../../subsystems/beatbox/README.md](../../subsystems/beatbox/README.md)
- [../../subsystems/speakers/README.md](../../subsystems/speakers/README.md)
- [../../audit/DOCUMENT_CORPUS_SUBSYSTEM_AUDIT.md](../../audit/DOCUMENT_CORPUS_SUBSYSTEM_AUDIT.md)
- [../../TRUST_BUNDLE_SPEC.md](../../TRUST_BUNDLE_SPEC.md)
