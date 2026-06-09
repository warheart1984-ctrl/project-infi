# Gate of Wonder Contract

**Version:** 1.0  
**Status:** Normative  
**Module:** `aais.wonder.gate`

## Purpose

The Gate of Wonder is a pre-logical constitutional imagination filter. It evaluates unstructured conceptual material — prompts, intents, hypotheses, and claim/reasoning text — before structured reasoning (RLS) and before action (OTEM). Wonder permits conceptual exploration; it never approves execution.

## Defensive-only invariant

Wonder returns verdicts only. It does not mutate external state, write quarantine records, or enqueue execution.

## ConceptualPossibility (v1)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `packet_id` | string | no | Source packet identifier |
| `packet_type` | string | yes | Bridge packet type |
| `spans` | array | yes | Extracted imagination text spans |
| `source_fields` | string[] | no | Payload keys that contributed spans |

### Span

| Field | Type | Required |
|-------|------|----------|
| `text` | string | yes |
| `field` | string | no |

## WonderVerdict (v1)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verdict` | enum | yes | `permit` \| `sandbox` \| `forbid` |
| `mode` | enum | yes | `lightweight` \| `governed` \| `paranoid` \| `hyper_strict` |
| `violations` | array | no | WonderViolation records |
| `summary` | string | no | Human-readable outcome |
| `evaluated_at` | string (ISO-8601) | no | Evaluation timestamp |

### WonderViolation

| Field | Type | Required |
|-------|------|----------|
| `code` | string | yes |
| `severity` | enum | yes | `info` \| `warning` \| `error` |
| `category_id` | string | yes |
| `matched_span` | string | no |
| `detail` | string | no |
| `invariant_id` | string | no |

## Forbidden category taxonomy

Wonder-specific pre-logical categories:

| Category | Typical outcome | Description |
|----------|-----------------|-------------|
| `meta_constitutional_breach` | forbid | Rewrite constitution; constraints do not apply; suspend invariants |
| `authority_usurpation` | forbid | Remove or bypass operator; eliminate human oversight |
| `immune_bypass_imagination` | forbid | Imagine disabling safety, guards, or immune response |
| `ceiling_expansion_fantasy` | forbid | Grant self authority; raise own ceiling without operator |
| `epistemic_unsafe_exploration` | sandbox (governed+) | Hedged exploration of bypassing forbidden actions |

Constitutional invariant IDs from RLS (`human_principal_root`, `defensive_only`, etc.) may appear on violations when patterns overlap.

## Mode bands

Wonder mode follows OTEM authority bands (mirrors RLS):

| Band | Wonder mode |
|------|-------------|
| autonomous | lightweight |
| governed | governed |
| containment | paranoid |
| sovereign | hyper_strict |

In `paranoid` and `hyper_strict` modes, `sandbox` verdicts are treated as `BLOCK` at the cognitive bridge.

## Relationship to RLS

Wonder is an **upstream precondition**. RLS must not run when Wonder returns `forbid`. RLS evaluates structured reasoning graphs; Wonder evaluates unstructured imagination text.

## Integration surfaces

1. **Cognitive bridge** — `generation_request`, `deliberation_request`, `reasoning_packet_ingress`
2. **Invariant compiler** — `wonder_gate` ingress validator (first in chain)
3. **Governed LLM** — defense-in-depth on `forbid` and `sandbox`+paranoid
4. **OTEM** — escalation metadata and gate checks alongside RLS
5. **API** — `/api/wonder/status` posture surface

## Schema

Normative JSON schema: `schemas/wonder_gate.v1.json`
