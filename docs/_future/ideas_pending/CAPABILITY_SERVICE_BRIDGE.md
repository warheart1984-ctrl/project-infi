# Capability Service Bridge

CISIV stage: **concept**

Status: pending — not yet integrated into active AAIS doc tree as a first-class subsystem family.

## 1. Purpose

Formalize the **seeded execution-governance fabric** in
[`src/capability_service_bridge.py`](../../../src/capability_service_bridge.py) as a
governed subsystem family: phase-gated capability admission, auditable service-lane
routing, and lineage-visible `capability_call` emissions for the CISIV Operator
Lineage Console.

The bridge already executes in production paths; this admission documents the
contract, proof posture, and promotion path without changing runtime behavior.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Subordinate to [AAIS_MODULE_GOVERNANCE_PROTOCOL.md](../../contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
and `src/phase_gate.py`. The bridge may block or degrade capability execution; it
does not override operator supremacy or Jarvis routing law.

## 3. Non-Goals

- No new capability modules in concept stage
- No bypass of phase gate or genome DNA checks at `governed` stage
- No replacement for raw HTTP or tool traces in [AAIS_TRACING_PROTOCOL.md](../../contracts/AAIS_TRACING_PROTOCOL.md)
- No autonomous promotion of arbitrary code into the capability registry

## 4. Bridge Contract

Schema: [schemas/capability_service_bridge.v1.json](./schemas/capability_service_bridge.v1.json)

| Field | Role |
|-------|------|
| `bridge_id` | Stable fabric id (`aais.capability_service_bridge`) |
| `component_id` | Phase-gate component registration |
| `governance_mode` | `strict` \| `assist` \| `experimental` |
| `service_path` | Ordered lane labels from selection through `tool_result` |
| `capability_call` | Auditable call envelope for lineage emission |

Default service path (implementation reference):

```text
selection → capability_registry → capability_service_bridge → module.execute → tool_result → response_trace
```

## 5. Phase Gate And Audit Integration

| Surface | Module |
|---------|--------|
| Component registration | `CapabilityServiceBridge` + `ConfiguredCapabilityModule` |
| Phase assertions | `assert_executable`, `assert_routable` via `src/phase_gate.py` |
| Audit ring buffer | `MAX_AUDIT_EVENTS` bounded events per bridge instance |
| Lineage hook | `capability_call` nodes → [CISIV_OPERATOR_LINEAGE_CONSOLE.md](./CISIV_OPERATOR_LINEAGE_CONSOLE.md) |

## 6. Operator Surfaces (Proposed)

| Surface | Path |
|---------|------|
| Inspect bridge status | `GET /api/jarvis/capability-bridge/status` (planned) |
| Governance gate | `make capability-bridge-gate` (planned) |
| Lineage lane | `python -m tools.ul.drift --lane capability_bridge` (planned) |

## 7. Failsafe

- Unregistered capability → `blocked` outcome; no silent execute
- Phase violation → `PhaseViolationError`; auditable phase event appended
- Degraded governance mode → explicit in bridge snapshot; never implied as `strict`
- Missing lineage emission → graph gap labeled; observe-only in lineage v1

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers bridge envelope, call record, and phase events | `asserted` | Schema + this document |
| Phase gate blocks unregistered components on fixture path | `none_yet` | Requires structure stage |
| Lineage console ingests `capability_call` from live bridge | `none_yet` | Requires verification |
| Dedicated governance gate passes in CI | `none_yet` | Requires implementation |

Target proof packet: `docs/proof/platform/CAPABILITY_SERVICE_BRIDGE_V1_PROOF.md` (not yet created).

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan + genome |
| Identity | Bridge id + component id frozen in active doc |
| Structure | Status API + governance gate stub |
| Implementation | Lineage emission contract + gate green |
| Verification | V1 proof + `make capability-bridge-gate` |

## 10. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AAIS_MODULE_GOVERNANCE_PROTOCOL.md](../../contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
- [CISIV_OPERATOR_LINEAGE_CONSOLE.md](./CISIV_OPERATOR_LINEAGE_CONSOLE.md)
- [AAIS_SUBSYSTEM_SPEC.md](../../runtime/AAIS_SUBSYSTEM_SPEC.md) §7 Barebones Map

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** **1** of 3 (`barebones-summon-wave-2026-06`)

**Depends on:** `phase_gate`, `module_governance` (live code; not genome-registered)

**Minimal invariants:**

- Every capability execute path routes through phase assertions when bridge is authoritative
- `governance_mode` is explicit in every exported snapshot
- Lineage `capability_call` nodes carry `cisiv_stage` at emission time
