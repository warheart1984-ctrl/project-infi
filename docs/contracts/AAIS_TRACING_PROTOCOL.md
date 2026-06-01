# AAIS Tracing Protocol

## Purpose

This file defines the active AAIS tracing contract for governed runtime flow.

Tracing in AAIS is the proof layer between:

- input normalization
- governance enforcement
- lane execution
- validation
- final visibility

Its job is not to make the system look observable.

Its job is to make every meaningful decision inspectable.

## Canonical Law

AAIS tracing exists to prove these runtime rules:

1. no execution without governance
2. no mutation outside declared contracts
3. all transitions must be pre-declared
4. all meaningful actions must be traceable
5. fail closed on uncertainty

Tracing is therefore not optional ornamentation.

It is part of runtime correctness.

## Active Runtime Truth

The live tracing spine is already structured in code.

Current active trace surfaces include:

- [`src/cognitive_bridge.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/cognitive_bridge.py>)
  - normalized input packets
  - deterministic governance packets
  - doctrine path and invariant trace
  - governed event results
  - governed LLM proposal envelopes for generation and deliberation packets
  - bridge decision trace
- [`src/governed_direct_pipeline.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_direct_pipeline.py>)
  - forward, service, and return packets
  - `bridge_hops` for swarm, LLM/service lane, and predictor traffic
  - pipeline validation and operator-health trace context
- [`src/governed_event_chain.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_event_chain.py>)
  - predictor -> invariant -> immune chain results
- [`src/immune_system.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_system.py>)
  - structured immune observations through `observe_protocol_signal`
- [`src/seam_log.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/seam_log.py>)
  - seam-level trace records

## Canonical Flow

The canonical AAIS tracing path is:

`input -> bridge -> law/invariants -> proposal or lane execution -> validation -> commit or block`

In admitted AAIS language, that means:

1. normalize the input into one governed packet shape
2. emit a governance packet
3. run the bounded governed event chain
4. record lane traffic and bridge hops
5. record validation outcome
6. expose final allow, degrade, or block state

No meaningful runtime path should bypass this order.

## Canonical Trace Units

### 1. Input Packet

Every traced ingress should resolve into this minimum shape before execution:

```json
{
  "source": "string",
  "type": "string",
  "payload": {},
  "requires_approval": true,
  "risk": "low|medium|high|critical"
}
```

This is the bridge-facing boundary packet.

It is the required common language for:

- LLM-originated requests
- predictor-originated requests
- swarm-originated requests
- service/tool lane requests
- reasoning ingress

### 2. Governance Packet

The bridge emits one deterministic governance packet per routed input.

Minimum required fields:

- `bridge_id`
- `bridge_version`
- `packet_fingerprint`
- `source`
- `packet_type`
- `intent`
- `execution_intent`
- `runtime_context`
- `lane`
- `risk`
- `requires_approval`
- `approval_granted`
- `effectful`
- `payload_fingerprint`
- `doctrine_path`
- `invariants`
- `bounded`

This is the canonical trace artifact for governance admission.

### 3. Governed Event Result

Every traced runtime packet must have a visible law/invariant result.

Minimum governed event outcome fields:

- `status`
- `decision`
- `runtime_context`
- `event`
- `prediction`
- `invariant_result`
- `immune_action` when escalation occurs
- `phase_gate`

### 4. Lane Packet Trace

The governed direct pipeline records packet flow explicitly across:

- `forward_packets`
- `service_packets`
- `return_packets`

These packets prove:

- which lane was active
- whether tool traffic stayed isolated
- whether Jarvis authority remained in path
- whether direct cognition stayed tool-free

### 5. Bridge Hops

`bridge_hops` are the compact trace proof that upstream cognitive sources did
not bypass governance.

Current live bridge-hop sources include:

- `swarm`
- `llm` or `service_lane`
- `predictor`

Every hop must end in:

- `ALLOW`
- `DEGRADE`
- or `BLOCK`

Never silent execution.

## Stage Hierarchy

The raw `tracing.docx` proposed lane spans and module spans.

AAIS keeps that hierarchy, but expresses it in admitted governed form.

### Required stages

- `intent`
- `doctrine`
- `invariants`
- `governance_packet`
- `decision`

### Recommended module-level spans or equivalent structured records

- `orchestrator`
- `predictor`
- `law_gate`
- `planner` when present
- `renderer`
- `validator`
- `io_commit`
- `adapter:<name>` when an adapter performs meaningful work

AAIS may represent these as explicit spans, packet traces, or structured stage
records, but the meaning must remain visible.

## What Must Be Traced

Trace:

- state-changing runtime actions
- governance decisions
- invariant decisions
- immune escalations
- tool execution requests and results
- review/apply or repo-change boundaries
- validator outcomes
- final completion or final block decisions

## What Should Not Be Traced As First-Class Runtime Events

Do not elevate the following into noisy first-class traces unless they become
meaningful to law or mutation:

- pure reads
- cheap cache hits
- internal helper calls
- formatting-only helper passes
- non-governing local convenience transforms

The goal is legible runtime proof, not telemetry clutter.

## Determinism Rule

Repeated runs of the same governed input should produce:

- the same normalized packet shape
- the same governance packet fingerprint inputs
- the same doctrine and invariant trace surfaces
- the same traced decision class unless runtime context truly changed

Tracing must help reveal drift, not introduce it.

## Failure Rule

If trace context is missing where governance requires it:

- the path must fail closed
- the runtime should block or degrade
- the missing trace state becomes a governance problem, not an invisible footnote

Tracing is therefore a contract dependency for effectful execution.

## OpenTelemetry And Jaeger

The source `tracing.docx` includes a drop-in OpenTelemetry/Jaeger proposal.

That proposal is valid as an export layer, but it is not the canonical AAIS
truth by itself.

Canonical rule:

- structured governed trace artifacts come first
- external exporters may mirror them
- external telemetry must not replace local governed trace visibility

If OTEL is added later, it should wrap the existing governed stages rather than
invent a separate observability language.

## Source Lineage

This contract was admitted from:

- [tracing.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/tracing.docx>)

The raw document proposed:

- lane-centric tracing
- module-level spans
- Jaeger/OTLP export
- mutation-versus-noise tracing discipline

This markdown file converts that into active AAIS language and aligns it with
the live bridge, governed direct pipeline, and governed event chain.
