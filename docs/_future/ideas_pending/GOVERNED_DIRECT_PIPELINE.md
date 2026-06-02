# Governed Direct Pipeline

CISIV stage: **concept**

Status: pending — not yet integrated into active AAIS doc tree as a first-class subsystem family.

## 1. Purpose

Formalize the **seeded packet and lane fabric** in
[`src/governed_direct_pipeline.py`](../../../src/governed_direct_pipeline.py) as a
governed subsystem family: explicit direct cognitive traffic vs service/tool lanes,
inspectable packet traces, immune-protocol hooks, and realtime signal feeds without
replacing the existing runtime.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Subordinate to [AAIS_IMMUNE_PROTOCOL.md](../../contracts/AAIS_IMMUNE_PROTOCOL.md) and
continuity witness inputs. Slower service/tool work stays off the direct cognitive
fast lane unless explicitly routed.

## 3. Non-Goals

- No replacement of the full Jarvis turn loop in concept stage
- No ungoverned bypass of immune protocol on packet build
- No OTEM or predictive lane activation without separate admission
- No silent merge of `direct_cognitive` and `service_tools` lanes in traces

## 4. Pipeline Contract

Schema: [schemas/governed_direct_pipeline.v1.json](./schemas/governed_direct_pipeline.v1.json)

| Constant | Value |
|----------|-------|
| `PIPELINE_ID` | `aais.governed_direct_pipeline` |
| `DIRECT_COGNITIVE_LANE` | `direct_cognitive` |
| `SERVICE_TOOL_LANE` | `service_tools` |

Core builders (implementation reference):

- `build_pipeline_packet` — single packet envelope
- `build_governed_turn_pipeline` — full turn trace with forward/return packets
- `_build_realtime_signal_feed` — risk and immune posture snapshot

Node labels include `LLM`, `God Brain`, `Jarvis`, `Nova`, `Predictor`, `Service Lane`.

## 5. Lane Separation Model

```text
direct_cognitive:  core forward/return packets (GB ↔ Jarvis ↔ Nova)
service_tools:     capability/tool forward/return (off fast lane)
```

| Integration | Module |
|-------------|--------|
| Immune hook | `src/immune_protocol.apply_immune_protocol` |
| Continuity | `src/continuity_witness.build_continuity_witness_input` |
| Capability lane | `src/capability_service_bridge.py` (service path) |
| Memory context | `src/jarvis_memory_board.py` (turn context) |

## 6. Operator Surfaces (Proposed)

| Surface | Path |
|---------|------|
| Turn pipeline inspect | `GET /api/jarvis/pipeline/{turn_id}` (planned) |
| Governance gate | `make governed-pipeline-gate` (planned) |
| Tests | `tests/test_governed_direct_pipeline.py` (extend for gate claims) |

## 7. Failsafe

- Immune `blocked` response → packets reflect degraded state; no silent `stable`
- Invalid signal feed → `_validate_realtime_signal_feed` marks validation failures
- Lane bleed (tool call on direct lane without route) → visible in packet `intent`
- Missing prior pipeline state → `_previous_pipeline_state` returns explicit empty shell

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers lanes, packets, and signal feed | `asserted` | Schema + this document |
| Turn builder separates direct vs service lanes on fixture | `none_yet` | Requires structure stage |
| Immune hook applied on every governed turn build | `none_yet` | Requires verification |
| Dedicated governance gate passes in CI | `none_yet` | Requires implementation |

Target proof packet: `docs/proof/platform/GOVERNED_DIRECT_PIPELINE_V1_PROOF.md` (not yet created).

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan + genome |
| Identity | Lane names + operation codes frozen in active doc |
| Structure | Inspect API + governance gate |
| Implementation | Universal turn pipeline export on governed paths |
| Verification | V1 proof + `make governed-pipeline-gate` |

## 10. Related

- [AAIS_IMMUNE_PROTOCOL.md](../../contracts/AAIS_IMMUNE_PROTOCOL.md)
- [CAPABILITY_SERVICE_BRIDGE.md](./CAPABILITY_SERVICE_BRIDGE.md)
- [JARVIS_MEMORY_BOARD.md](./JARVIS_MEMORY_BOARD.md)
- [AAIS_SUBSYSTEM_SPEC.md](../../runtime/AAIS_SUBSYSTEM_SPEC.md) §7 Barebones Map

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** **3** of 3 (`barebones-summon-wave-2026-06`)

**Depends on:** **Capability Service Bridge** (order 1), **Jarvis Memory Board** (order 2); immune protocol (live)

**Minimal invariants:**

- Every governed turn trace names its lane per packet
- Service/tool traffic uses `service_tools` unless explicitly dual-routed
- Signal feed carries `risk_level` and immune response when immune hook runs
