# Velvet System Contract (VS-01)

**Engineering class:** `RuntimeSystemLaw` / `LawfulTurn` (Nova lawful runtime)  
**Mythic label:** Velvet System — expression under consequence

## Invariants

1. **Four expression systems** — observe, reason, summarize, files (capability-gated; no silent expansion).
2. **Nothing is free** — every admitted turn carries `cost`, `trace`, and `consequence` metadata.
3. **Cost / trace / consequence on every action** — surfaced on HTTP chat JSON and in `LawfulTurn`.
4. **No clean resolution** — governance denials return structured RSL codes; no bypass via alternate chat stacks.

## Stage 1 scope

- Default chat (`POST /api/chat/sessions/{id}/message`) uses Nova `LawfulLLM.ask()` only.
- Legacy cognitive bridge, slingshot, mechanic, OTEM ceiling, and composed-turn gates are **not** on the default path.
- VS-01 metadata is **deterministic stubs** derived from RSL receipt (not a second billing runtime).

## Failure modes

| Condition | RSL / behavior |
|-----------|----------------|
| Missing tenant | `RSL-TENANT-REQUIRED` |
| Disallowed capability | `RSL-CAPABILITY-DENIED` |
| Prompt over limit | `RSL-PROMPT-LIMIT` |
| Detachment attempt | `RSL-DETACHMENT-DENIED` + session review hold |
| Review hold active | `RSL-TEMPORARY-REVIEW-DENY` |

## Non-responsibilities

- Story Forge / Movie Renderer production pipelines (scaffold only).
- darz-kernel proof obligations.
- Runtime artifact attestation (cog-os).
