# ARIS standalone service — admission spec (v1)

Status: **partial** (MVP sidecar + gate path live; criteria 3–4 and live admission tests open)

Authority: [ARIS_RUNTIME_CONTRACT.md](./ARIS_RUNTIME_CONTRACT.md), [AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md) §4

## Purpose

Move **standalone ARIS** from **blocked** to **admitted-for-build** under AAIS law. Embedded ARIS remains the enforcement spine; a standalone service is an optional satellite that must not duplicate or bypass bridge authority.

## Current state

| Form | Status |
|------|--------|
| Embedded ARIS (bridge + law surfaces) | **Live** — see [ARIS_RUNTIME_CONTRACT.md](./ARIS_RUNTIME_CONTRACT.md) |
| Standalone ARIS daemon / sidecar | **Pilot MVP** — `aris_service/__init__.py`; full admission criteria 3–5 open |

## Admission criteria (all required)

### 1. Contract boundary

- [x] Standalone service exposes **read/analyze/suggest** only — no direct runtime mutation (MVP `/v1/admit`)
- [x] All write paths route through **external suggestion admission** ([EXTERNAL_SUGGESTION_ADMISSION_RULE.md](./EXTERNAL_SUGGESTION_ADMISSION_RULE.md)) (via `build_aris_enforcement`)
- [ ] Non-copy clause enforced: no raw outside prose into architecture truth

### 2. AAIS Immune + genome

- [x] Governed genome registered with `stage: governed` or explicit pilot genome with SSP bundle (`governance/subsystem_genomes/aris_standalone_service.genome.v1.json`)
- [x] `make aris-standalone-gate` passes (`.github/scripts/check-subsystem-mvp-integration-governance.py`) — use Python 3.12 on Windows when `python3` is absent
- [ ] Subsystem spec delta filed in [PROJECT_BLUEPRINTS_MASTER.md](../../document/blueprints/PROJECT_BLUEPRINTS_MASTER.md)

### 3. Build / runtime split

- [ ] Build artifacts (indexes, repo snapshots) versioned separately from runtime session state
- [ ] Runtime service loads artifacts read-only; no self-apply of suggestions

### 4. Security membrane

- [ ] Service authenticates as **tenant-scoped** operator identity — no cross-tenant repo access
- [ ] Network: private service or Platform membrane route — not public unauthenticated ingress

### 5. Proof bundle

- [ ] `docs/proof/platform/ARIS_STANDALONE_V1_PROOF.md` with:
  - [ ] Admission test: external suggestion rejected without law filter
  - [ ] Admission test: admitted abstract/signature-only pattern accepted
  - [x] Gate output: `make aris-standalone-gate` (14 passed via Python 3.12, 2026-06-08)

## Unblock procedure

1. **Design review** — confirm standalone does not fork [cognitive_bridge.py](../../src/cognitive_bridge.py) authority
2. **Implement MVP** — repo intelligence API behind Platform or AAIS proxy
3. **Run gates** — genome + `aris-standalone-gate` + flagship verification subset
4. **Update maps** — remove "blocked" row in [SUBSYSTEMS_REMAINING_MAP.md](../runtime/SUBSYSTEMS_REMAINING_MAP.md); set state to **admitted** or **pilot**
5. **Blueprint delta** — [BLUEPRINT_DELTA_CHECKLIST.md](../../document/compliance/BLUEPRINT_DELTA_CHECKLIST.md)

## Non-goals (v1 admission)

- Replacing embedded `aris_integration.py` paths
- Cross-org pattern export without collective ledger rules
- Autonomous code apply without OTEM / workflow approval

## Phase alignment

[STRATEGY.md](../spine/STRATEGY.md) Phase 4 — ARIS standalone moves from blocked → admitted when criteria 1–5 are **proven**, not when code exists alone.

## Related

- [COLLECTIVE_PATTERN_LEDGER.md](./COLLECTIVE_PATTERN_LEDGER.md)
- [SUBSYSTEMS_REMAINING_MAP.md](../runtime/SUBSYSTEMS_REMAINING_MAP.md)
