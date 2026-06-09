# Reasoning & Logic Substrate (RLS) Contract

**Version:** 1.0  
**Status:** Normative  
**Module:** `aais.rls`

## Purpose

RLS is the epistemic counterpart to OTEM. OTEM governs whether an action may be taken; RLS governs whether a reasoning chain is admissible enough to justify that action. Rejected reasoning must not become a valid OTEM proposal or pass governed ingress without quarantine.

## Defensive-only invariant

RLS returns verdicts only. It never enqueues execution, mutates external state, or auto-approves operators.

## ReasoningGraph (v1)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Stable graph identifier |
| `version` | string | yes | Schema version (`1.0`) |
| `timestamp` | string (ISO-8601) | yes | Graph construction time |
| `source` | enum | yes | `jarvis` \| `external` \| `otem_justification` |
| `nodes` | array | yes | Premise, inference, conclusion nodes |
| `edges` | array | yes | Directed support/derivation links |
| `conclusion_id` | string | yes | Terminal conclusion node id |
| `proposed_action` | object | no | OTEM/governance intent being justified |

### Node

| Field | Type | Required |
|-------|------|----------|
| `id` | string | yes |
| `kind` | enum | yes | `premise` \| `inference` \| `conclusion` |
| `text` | string | yes |
| `evidence_refs` | string[] | no |

### Edge

| Field | Type | Required |
|-------|------|----------|
| `from` | string | yes |
| `to` | string | yes |
| `relation` | enum | yes | `supports` \| `derives` |

## RLSVerdict (v1)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verdict` | enum | yes | `admit` \| `downgrade` \| `reject` |
| `confidence_band` | enum | yes | UGR standing: `denied`, `hypothetical`, `asserted`, `proven` |
| `violations` | array | yes | Structured violation records |
| `mode` | enum | yes | `lightweight` \| `governed` \| `paranoid` \| `hyper_strict` |
| `graph_id` | string | yes | Source graph id |
| `otem_level` | integer | yes | OTEM capability level at evaluation |
| `quarantine_id` | string | no | Present when `verdict` is `reject` |
| `cannot_justify_escalation` | boolean | no | True when downgrade blocks OTEM justification |

### Violation

| Field | Type | Required |
|-------|------|----------|
| `code` | string | yes |
| `severity` | enum | yes | `info` \| `warning` \| `error` |
| `node_ids` | string[] | no |
| `detail` | string | yes |

### Violation codes (v1)

- `missing_evidence` — conclusion or critical inference lacks evidence refs
- `orphan_conclusion` — conclusion has no inbound support path
- `circular_reasoning` — cycle in support graph
- `self_justifying_loop` — conclusion or proposed action cited as sole evidence
- `unsupported_leap` — inference without premise support
- `constitutional_conflict` — violates OTEM constitutional invariant
- `monotonic_falsity_violation` — reasserts proven-false claim without override
- `speculative_at_ceiling` — speculative reasoning at sovereign/hyper_strict ceiling
- `missing_verdict` — fail-closed when verdict absent in governed+ bands

## Band modes

Derived from `authority_band()` in `otem_capability`:

| OTEM band | Levels | RLS mode | Escalation justification minimum |
|-----------|--------|----------|----------------------------------|
| autonomous | 1–9 | lightweight | Filter obvious nonsense |
| governed | 10–15 | governed | `admit` with band ≥ `asserted` |
| containment | 16–19 | paranoid | Aggressive drift flags; downgrade blocks high-risk |
| sovereign | 20 | hyper_strict | Evidence-backed only; `admit` requires `proven`-equivalent |

## Fail-closed rule

In bands `governed`, `containment`, and `sovereign`, a missing RLS verdict is treated as `reject` (same posture as constitutional `fail_closed`).

## Evidence refs (v1)

Accepted prefixes: `odl:`, `ugr:`, `ir:`, `log:`, `external:`. Unresolved refs downgrade in lightweight mode; reject in paranoid/hyper_strict when the conclusion depends on them.

## Monotonic truth

Proven-false claims are stored in the falsity registry. Reintroduction without `operator_override` + `new_evidence_refs` yields `monotonic_falsity_violation` → `reject`.

## Upstream: Gate of Wonder

RLS runs only after the **Gate of Wonder** (`aais.wonder.gate`) clears imagination-bearing ingress. Wonder filters unstructured prompts, intents, and hypothesis text for pre-logical constitutional violations. When Wonder returns `forbid`, RLS must not evaluate the packet.

See `docs/contracts/WONDER_CONTRACT.md` and `schemas/wonder_gate.v1.json`.

## Integration surfaces

1. **External ingress** — after `normalize_reasoning_exchange_packet`, before admission handshake
2. **Cognitive bridge** — after Wonder; `reasoning_packet_ingress` blocked on `reject`
3. **OTEM escalation** — approval enqueue requires `admit` (band-dependent)
4. **Jarvis deliberation** — graph attached at export; RLS before governed LLM / OTEM paths
5. **CheckGraph** — `rls_reasoning_admissible` validator at checkpoint/ingress

## Relationship to other organs

- **Reasoning Contract Organ** — read-only posture; RLS is the active evaluator
- **Reasoning Exchange Protocol** — transport boundary; RLS is epistemic gate
- **UGR standing** — confidence vocabulary for RLS output
