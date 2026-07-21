# VEILTHORN Stage 1 Spec

Status: Draft
Scope: Stage 1 only
Follow-on: Stage 2 is defined at the end of this spec and is explicitly out of scope for implementation in this sprint

## 1. Summary

VEILTHORN-RUNTIME becomes the reference implementation for the CIEMS Proof Surface by exposing a verifiable, developer-friendly runtime contract around every inference response.

Stage 1 focuses on the external verification spine:

1. Developer Experience
2. Runtime Proof Surface
3. REST API reference
4. OpenAPI specification
5. Postman collection
6. Sample clients and sample prompts
7. Conformance Suite

This stage is documentation-first, contract-first, and proof-first. It makes the runtime easy to install, easy to call, easy to inspect, and easy to verify before any broader operator dashboard work begins.

## 2. Background

The repo already has a governed runtime spine, docs-site architecture pages, scorecards, and proof-oriented language around replay and evidence. Stage 1 should extend those existing surfaces rather than create a second documentation system.

The current runtime work has already crossed from architecture into a working execution substrate. The next step is to make the surface independently verifiable for outside users:

1. A new developer can get a local runtime running quickly.
2. A client can call the runtime using a documented REST contract.
3. Every inference response can produce proof metadata that supports verification and replay.
4. Supported backends can be tested against a published conformance suite.

## 3. Goals

Stage 1 must deliver the following outcomes:

1. A 5-minute local setup path that gets a developer from clone to first successful request.
2. Canonical API documentation for the current runtime surface.
3. Example clients in C++, Python, and TypeScript that match the documented API.
4. A machine-readable OpenAPI document that describes the REST surface.
5. A Postman collection that exercises the same canonical endpoints as the docs.
6. A proof surface embedded in inference responses.
7. A conformance suite that defines what it means for a backend to be supported.

## 4. Non-Goals

Stage 1 does not include:

1. A live operator dashboard.
2. Pilot packaging beyond the documentation and proof contracts needed for Stage 1.
3. New inference features unrelated to proof or verifiability.
4. A separate docs system outside the existing docs-site and repo docs tree.
5. Replacing the runtime architecture with a new stack.

## 5. Design Principles

1. Contract first: documentation and response shape must agree.
2. Proof first: every public inference response should carry enough metadata to audit and replay the action.
3. Minimal surface area: do not add runtime complexity that does not help verification.
4. One canonical path: example clients should all point to the same documented REST endpoint family.
5. Stage separation: anything visual, operational, or pilot-packaging heavy belongs in Stage 2.

## 6. Repo Integration Strategy

Stage 1 should extend the existing repo surfaces in place:

1. `docs-site/docs` becomes the main human-facing documentation tree for VEILTHORN.
2. The runtime implementation remains the source of truth for API behavior.
3. The proof surface contract is documented in the docs site and enforced in runtime responses.
4. The conformance suite lives with the runtime and gates backend support claims.

This spec intentionally avoids a parallel docs system. It assumes the Stage 1 materials are additions to the current workspace docs, not replacements for them.

## 7. Developer Experience

### 7.1 Quick Start

The quick start must let a new developer get to a first successful response in roughly 5 minutes.

Required contents:

1. Prerequisites.
2. Clone and install steps.
3. Runtime start command.
4. First `curl` or equivalent request.
5. Expected success response.
6. Minimal troubleshooting notes.

The quick start should emphasize the canonical local path, not multiple alternative setup flows.

### 7.2 Example Clients

Provide one minimal example client in each of:

1. C++
2. Python
3. TypeScript

Each client must:

1. Call the same documented inference endpoint.
2. Include a simple prompt.
3. Print the completion and proof metadata.
4. Show how to inspect verification status and governance decision.

The examples should be copyable, minimal, and directly tied to the API reference.

### 7.3 Sample Prompts and Responses

Include a short set of sample interactions that demonstrate:

1. A normal inference request.
2. A backend selection case.
3. A governance rejection or delay case.
4. A proof receipt example.

These samples should match the runtime response envelope that Stage 1 defines.

## 8. REST API Reference

The REST reference must describe the current runtime surface in a stable, documented way.

Minimum documented endpoints:

1. `GET /health`
2. `GET /backends`
3. `GET /v1/models`
4. `POST /v1/generate`
5. `POST /v1/chat/completions`

The reference must document:

1. Request shape.
2. Response shape.
3. Error conditions.
4. Governance-related response fields.
5. Proof-related response fields.
6. Status codes.

The API reference should identify `POST /v1/chat/completions` as the canonical external inference path unless the runtime later makes a different endpoint the primary contract. Stage 1 should not introduce a second canonical inference path.

## 9. OpenAPI Specification

Stage 1 must publish an OpenAPI spec that matches the documented REST surface.

Requirements:

1. The spec must be machine-readable.
2. The spec must describe the canonical inference request and response schemas.
3. The spec must include the proof surface fields.
4. The spec must be suitable for generating client stubs and Postman collections.

The OpenAPI document is not just a docs artifact. It is part of the contract that keeps the runtime, clients, and examples aligned.

## 10. Postman Collection

Provide a Postman collection that covers the core runtime paths:

1. Health check.
2. Backend listing.
3. Model listing.
4. Generate request.
5. Chat completion request.

The collection should use the same field names and URLs as the OpenAPI spec and API reference.

## 11. Runtime Proof Surface

Every inference response should expose the information needed to verify and replay what happened.

### 11.1 Required Response Fields

The proof surface must expose at least:

1. `runtime_version`
2. `backend`
3. `model`
4. `proof_level`
5. `evidence_receipt`
6. `replay_id`
7. `verification_status`
8. `governance_decision`
9. `resource_usage`

### 11.2 Field Semantics

1. `runtime_version`: identifies the runtime build or release version that produced the response.
2. `backend`: identifies the backend that actually executed the inference.
3. `model`: identifies the model name or identifier used for the request.
4. `proof_level`: identifies the proof maturity level, using the `P0` through `P5` scale.
5. `evidence_receipt`: a structured proof artifact or receipt identifier that links the response to evidence.
6. `replay_id`: a stable replay identifier that allows the event to be reconstructed or referenced.
7. `verification_status`: indicates whether the response is verified, pending, degraded, rejected, or equivalent.
8. `governance_decision`: records the policy or routing outcome that governed the request.
9. `resource_usage`: records the resources consumed by the request, at minimum including latency and memory or VRAM usage when available.

### 11.3 Proof Level

Use a six-level proof maturity scale:

1. `P0` - no proof surface
2. `P1` - basic metadata only
3. `P2` - structured receipt present
4. `P3` - replayable receipt with governance linkage
5. `P4` - conformance-backed proof surface
6. `P5` - externally verifiable and reference-grade proof surface

Stage 1 should target the proof level that is honestly supportable by the runtime and conformance suite at the time of implementation. The spec should not claim a higher proof level than the evidence supports.

## 12. Conformance Suite

Before a backend is called supported, it must pass the conformance suite.

### 12.1 Required Coverage

1. Functional correctness.
2. Determinism.
3. Replay verification.
4. Resource limits.
5. Failure recovery.
6. Governance enforcement.
7. Performance baseline.

### 12.2 Support Policy

The conformance suite must answer:

1. Is the backend functional?
2. Is the backend deterministic enough for the declared proof level?
3. Can the response be replayed from its evidence receipt and replay ID?
4. Does the backend respect configured resource limits?
5. Does the backend fail safely and recover cleanly?
6. Does the backend obey governance decisions?
7. Does the backend meet the minimum performance baseline for support?

### 12.3 Supported Backend Definition

A backend is not "supported" because it exists in code. It is supported only when the conformance suite passes for the declared proof level and resource envelope.

## 13. Acceptance Criteria

Stage 1 is complete when all of the following are true:

1. The docs-site contains a clear VEILTHORN quick start.
2. The docs-site contains a REST API reference for the canonical runtime surface.
3. The docs-site contains sample prompts and responses.
4. The docs-site links to an OpenAPI specification.
5. The docs-site links to or embeds a Postman collection.
6. The runtime response envelope includes the required proof surface fields.
7. Example clients exist in C++, Python, and TypeScript and are consistent with the docs.
8. The conformance suite exists and is runnable.
9. Supported backend claims are backed by the conformance suite.
10. Stage 2 remains explicitly deferred and unimplemented.

## 14. Testing Strategy

The implementation should be validated with:

1. Documentation presence checks.
2. Schema consistency checks between docs and OpenAPI.
3. Example client smoke tests.
4. Runtime response shape tests.
5. Conformance suite tests.
6. Replay and evidence receipt checks for the proof surface.

The test strategy should fail if a docs page, OpenAPI schema, or sample client drifts from the runtime response contract.

## 15. Risks

1. Proof surface fields may drift if they are documented separately from the runtime response model.
2. The quick start can become inaccurate if setup instructions are not validated end to end.
3. Example clients can rot if they are not kept in lockstep with the API reference.
4. Backend support claims can become overstated if the conformance suite is not treated as the support gate.
5. Stage 2 work can leak into Stage 1 if dashboard or pilot packaging concerns are not kept out of scope.

## 16. Stage 2 Follow-On Plan

Stage 2 should build on the Stage 1 contract and add the operational surfaces:

1. Live observability dashboard.
2. Backend health panels.
3. CPU/GPU utilization views.
4. VRAM/RAM views.
5. Active request and queue depth views.
6. Latency trend views.
7. Governance event streams.
8. Evidence event streams.
9. Proof surface status panels.
10. External pilot kit packaging.
11. Docker image.
12. Benchmark suite packaging.
13. Troubleshooting guide.
14. Evidence report template.

Stage 2 should not redefine the proof contract. It should consume the proof contract that Stage 1 establishes.
