# Imagine Generator

CISIV stage: **implementation** (MVP live — see [../../subsystems/storyforge/IMAGINE_GENERATOR.md](../../subsystems/storyforge/IMAGINE_GENERATOR.md))

Status: partial live — pattern emit + Story Forge admission handoff. Proof: [../../proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md](../../proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md)

## 1. Purpose

Emit **governed imagination pattern** artifacts — structured prompt frames,
constraints, and CISIV-staged envelopes — that downstream creative lanes (primarily
Story Forge) can consume without treating raw model output as canonical truth.

Archive corpus material (`Imagine generator.docx`, `Imagine pattern.docx`) describes
pattern-based creative emission; this concept admits that family as a subordinate
lane under Story Forge authority, not as a sovereign creative subsystem.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Imagine Generator is **subordinate to Story Forge**. It proposes patterns; Story
Forge canonical docs and runtime own narrative build truth. Jarvis authorizes
capability calls that emit patterns.

## 3. Non-Goals

- Not a sovereign creative subsystem or bypass of Story Forge law
- Not a replacement for Story Forge canonical truth ([STORYFORGE_CANONICAL.md](../../subsystems/storyforge/STORYFORGE_CANONICAL.md))
- Not conflating vendored `grok-imagine-image` / `grok-imagine-video` adapter strings
  with this governed contract — those remain implementation lineage only
- No ungoverned free-form image/video generation without constraint envelope
- No Human Voice Extraction merge (separate pending family; activates later in batch)

## 4. Pattern Artifact Contract

Schema: [schemas/imagine_generator.v1.json](./schemas/imagine_generator.v1.json)

| Field | Role |
|-------|------|
| `imagine_generator_version` | Must be `imagine_generator.v1` |
| `pattern_id` | Stable pattern identifier |
| `pattern_type` | `scene_seed`, `character_beat`, `visual_motif`, `audio_cue`, `world_texture` |
| `prompt_frame` | Governed prompt body (max 8000 chars) |
| `constraints` | Forbidden terms, tone, rating caps, etc. |
| `downstream_hints` | Optional Story Forge lane / adapter lineage note |
| `ul_substrate` | Optional UL envelope attachment |
| `cisiv_stage` | Pattern-level CISIV summary |
| `claim_label` | Overall pattern posture |

Runtime layout (proposed):

```text
.runtime/imagine_generator/<pattern_id>/
  imagine_generator.v1.json
  pattern_ledger.jsonl
```

## 5. Story Forge Handoff

Patterns hand off to Story Forge as **inputs**, not as final cinematic truth:

- Story Forge validates pattern schema before admitting to build graph
- Rejected constraint violation → `claim_label: rejected`; no silent downgrade
- Beatbox / Speakers remain downstream of Story Forge, not of Imagine Generator directly

Structured capability envelope (future):

```json
{
  "capability": "imagine_generator",
  "pattern_type": "scene_seed",
  "mission_id": "mission-abc-001"
}
```

## 6. Constraint Model

Each constraint carries `constraint_kind` and optional per-constraint `claim_label`:

| Kind | Role |
|------|------|
| `forbidden_term` | Block listed tokens in downstream prompts |
| `required_element` | Must appear in admitted handoff |
| `tone` | Register / mood bound |
| `rating_cap` | Content rating ceiling |
| `length_cap` | Max expansion for prompt_frame derivatives |

## 7. Failsafe

- Constraint violation at emit time → `claim_label: rejected`; do not hand off
- Missing Story Forge lane when required by mission → halt with `asserted` partial
- Adapter failure (e.g. external image API) → record in ledger; do not overwrite pattern claim_label as `proven`
- Conflicting constraints → surface all; operator resolves

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers pattern types, constraints, and version const | `asserted` | Schema + this document |
| Fixture pattern validates and hands off to Story Forge stub | `none_yet` | Requires implementation |
| `make imagine-generator-gate` passes on demo pattern | `none_yet` | Requires structure stage |
| grok-imagine adapters documented as lineage only | `none_yet` | Requires implementation audit note |

Target proof packet: `docs/proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md` (not yet created).

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Identity | `pattern_id` tied to mission/session keys |
| Structure | `src/imagine_generator.py` + capability bridge hook |
| Implementation | Emit + Story Forge admit path |
| Verification | Fixture pattern with proven handoff edge |

## 10. Related

- [../../subsystems/storyforge/STORYFORGE_CANONICAL.md](../../subsystems/storyforge/STORYFORGE_CANONICAL.md)
- [../../subsystems/storyforge/NARRATIVE_TRUST_PACK.md](../../subsystems/storyforge/NARRATIVE_TRUST_PACK.md)
- [../../audit/DOCUMENT_CORPUS_SUBSYSTEM_AUDIT.md](../../audit/DOCUMENT_CORPUS_SUBSYSTEM_AUDIT.md) (Imagine Generator / Pattern — archive_only_high_signal)
- [../../../external/story_forge/src/story_forge/image_adapter/grok_adapter.py](../../../external/story_forge/src/story_forge/image_adapter/grok_adapter.py) (lineage only)
- Archive: `docs/_archive/workspace_pull/project-infi-root/Imagine generator.docx`, `Imagine pattern.docx`

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** 2 of 3 — after Recipe Module

**Depends on:** Story Forge subsystem pack (partial live), capability service bridge, optional Recipe Module packs for repeatable creative workflows

**Minimal invariants:**

- Imagine Generator does not replace Story Forge canonical truth
- Patterns are inputs; cinematic build truth remains Story Forge-owned
- Constraint violations block handoff
- Human Voice Extraction is out of scope for this family
