# ESFR PromotionEligibility — AAES Crew + CEF Phase 1 + Baseline

**Date:** 2026-07-31 (updated 2026-07-31: independent-reproduction prerequisites waived for this gate)  
**ModeKey:** `sage__navigator__evidence-strict`  
**Gate:** `aaes-esfr` (PromotionEligibility)  
**Scorecard:** [docs/scorecards/project-infi.md](../scorecards/project-infi.md)

## Claim boundaries reviewed

| Claim | Result | Evidence |
|-------|--------|----------|
| Lean AAES crew pack installed in project-infi | **pass** | `.cursor/aaes-crew/`, `.cursor/skills/aaes-*`, `.cursor/agents/aaes-*`, rules, root `AGENTS.md`, `IMPORT_SOURCES.md` |
| `@aaes-os/cef-core` Phase 1 (schemas + Ajv validators + tests) | **pass** | `packages/cef-core` tests (schema, profiles, promotion gate) |
| Production Baseline freeze structure + checksum re-verify | **pass** | `checksum-reverify.json` allMatched=true for k8s + workflow vs freeze |
| OEL evidence schema-bound via cef-core | **pass** | `oel-evidence-validated.json` + `cef-core-validation-receipt.json`; `promotion.decision: hold` (DRAFT certificate OK) |
| Independently reproduced live-cluster ops | **waived** (out of scope for this ESFR) | Not required for this gate; tooling remains optional backlog |
| GHCR digest pins / authority-signed ACTIVE certificate | **waived** (out of scope for this ESFR) | Not required for this gate; CI/cert stubs remain for later stewardship |
| Commercial / self-serve readiness | **not claimed** | Drive-G-2 audience note on baseline INDEX |

## Drive-G-2 snapshot (this slice only)

| Dimension | Rating | Audience |
|-----------|--------|----------|
| Constitutional model | Working (CEF charter + structural enforcement in cef-core) | operators / governance |
| Governance methodology | Partial (crew + ESFR declared; ModeKey not runtime-enforced) | operators |
| Reference implementation | Working for cef-core library; ops stack freeze only | operators |
| Platform engineering | Partial (manifests frozen; live digests/cluster optional) | operators |
| Commercial operations | Early / not claimed by this slice | users |

## Outcomes

- **pass** — Crew pack + cef-core Phase 1 + baseline freeze + schema-validated OEL (HOLD/DRAFT) for this ESFR gate  
- **waived for this gate** — CI digest fill, live cluster capture, authority-signed ACTIVE certificate  
- **still not claimed** — commercial / self-serve readiness; “production ready” without dimension + audience  

## Deferred backlog (optional — not ESFR blockers)

These remain available for later stewardship when desired; they are **not** PromotionEligibility prerequisites for this note:

1. Fill GHCR digests via `merge-image-digests` CI job  
2. Run `scripts/capture-baseline-live-evidence.ps1` against a cluster  
3. Authority-signed promotion to ACTIVE via `@aaes-os/cef-certification`  

## Follow-on slice (architect Priority 1–3) — implemented contracts

| Item | Status |
|------|--------|
| CI digest pin → `image-tags.json` | Contract landed (optional for this ESFR) |
| Live evidence pack + capture script | Structure landed (optional for this ESFR) |
| OEL promotion gate (claim≠evidence) | Enforced in library (ACTIVE path unused for this ESFR) |
| CEF consumer packages + OEL CI workflow | Landed |
| Profile fixtures CREC/CEL/Security/ModelEval | Landed |
| Foreman invoke template + scorecard + vendor sync | Landed |
