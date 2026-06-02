# Capability Service Bridge — MVP Plan

CISIV stage: concept → implementation target

Status: planned (not yet implemented)

Batch: `barebones-summon-wave-2026-06`

Concept origin: [./CAPABILITY_SERVICE_BRIDGE.md](./CAPABILITY_SERVICE_BRIDGE.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| module | `src/capability_service_bridge.py` | Exists — document as governed surface |
| api | `GET /api/jarvis/capability-bridge/status` | Read-only bridge + audit snapshot |
| gate | `make capability-bridge-gate` | Phase + schema coverage |
| lineage | `src/ul_lineage.py` | Emit `capability_call` on governed execute |

## 2. Code Artifacts

- `src/api.py` — register status route
- `.github/scripts/check-capability-bridge-governance.py` — gate script
- `tools/governance/check_capability_bridge.py` — optional wrapper

## 3. Tests

- `tests/test_capability_service_bridge.py` — extend: phase block, audit ring, snapshot schema
- `tests/test_ul_lineage.py` — capability_call node from bridge fixture

## 4. Fixtures

- `fixtures/capability_bridge/strict-allow.json` — allowed call under strict mode
- `fixtures/capability_bridge/phase-block.json` — unregistered component blocked

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make capability-bridge-gate` | `.github/scripts/check-capability-bridge-governance.py` | after `make genome-gate` |

## 6. Proof Bundle

Target: `docs/proof/platform/CAPABILITY_SERVICE_BRIDGE_V1_PROOF.md`

| Claim | Label | Evidence |
|-------|-------|----------|
| Status API returns schema-valid bridge envelope | `none_yet` | Requires implementation |
| Phase gate blocks fixture violation | `none_yet` | Requires verification |
| Lineage ingests capability_call | `none_yet` | Requires verification |

## 7. Reproduction Commands

```bash
python -m pytest tests/test_capability_service_bridge.py -q
make capability-bridge-gate
make genome-gate
```

## 8. Activation Dependencies

**Existing subsystems required:** `phase_gate`, `module_governance`, `cisiv_operator_lineage_console`

**Order among batch:** **1** — foundational execution governance before memory/pipeline formalization

**Rationale:** Service-lane routing and phase assertions are prerequisites for governed pipeline service packets and universal lineage coverage.
