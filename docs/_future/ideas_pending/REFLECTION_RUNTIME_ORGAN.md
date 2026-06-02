# Reflection Runtime Organ

CISIV stage: **concept**

Status: pending — Alt-5 summon wave 2 `alt5-summon-wave-2-2026-06`.

## 1. Purpose

Formalize the **Reflection Runtime** (`cognitive.reflection`) from
[NOVA_CORTEX.md](../../runtime/NOVA_CORTEX.md) as a governed Alt-5 organ: read-only
exposure of the expect → compare → learn → adjust loop spec and invariants without
competing with Jarvis authority.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Subordinate to Jarvis routing;
reflection evaluates coherence; it does not override operator supremacy.

## 3. Non-Goals

- No autonomous promotion of planning or execution without Jarvis authorize
- No replacement for full `src/cog_runtime/reflection.py` turn processing in v1
- No narrative or trust-pack synthesis in this organ

## 4. Organ Contract

Schema: [schemas/reflection_runtime_organ.v1.json](./schemas/reflection_runtime_organ.v1.json)

| Field | Role |
|-------|------|
| `runtime_id` | `cognitive.reflection` |
| `stages` | `expect`, `compare`, `learn`, `adjust` |
| `summary` | Cross-lobe alignment loop |

## 5. Runtime (Proposed)

- `GET /api/jarvis/reflection-runtime/status` — read-only spec snapshot
- `src/reflection_runtime_organ.py` — wraps `reflection_runtime_spec()`

## 6. Failsafe

Invalid or missing spec fields return structured errors; organ remains read-only.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns reflection snapshot | `none_yet` | Requires MVP |
| Stages match NOVA_CORTEX reflection lobe | `none_yet` | Requires verification |

Target proof packet: `docs/proof/cognitive_runtime/REFLECTION_RUNTIME_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/reflection_runtime_organ.py` stub |
| Implementation | API route + gate |
| Verification | V1 proof + `make reflection-runtime-gate` |

## 9. Related

- [NOVA_CORTEX.md](../../runtime/NOVA_CORTEX.md)
- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [SAFETY_ENVELOPE_ORGAN.md](./SAFETY_ENVELOPE_ORGAN.md)

## 10. Activation Order

**Batch:** `alt5-summon-wave-2-2026-06` — order **1** (meta-cognitive guard after Alt-5 wave 1)

**Depends on:** `safety_envelope_organ`, `operator_profile_organ` (Alt-5 wave 1)

**Minimal invariants:**

- Read-only v1 — no write path from reflection organ
- Stages frozen to expect/compare/learn/adjust in schema export
- Non-competing invariant from reflection runtime spec preserved in snapshot
