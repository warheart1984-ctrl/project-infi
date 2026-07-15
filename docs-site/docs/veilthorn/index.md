---
title: VEILTHORN Stage 1
slug: /veilthorn
description: Stage 1 documentation spine for VEILTHORN, focused on the docs, proof surface, and canonical inference path.
---

# VEILTHORN Stage 1

VEILTHORN Stage 1 is a documentation-only spine for the governed runtime reference surface.
It publishes the canonical docs path, the proof/challenge contract, and the OpenAI-compatible runtime family without claiming a live Stage 2 implementation.

## What Stage 1 covers

- A docs landing page for the VEILTHORN reference set
- A quick start for reading and verifying the doc surface
- An API reference for the documented endpoint family
- A proof surface that keeps claim, evidence, and invalidation evidence separate
- Examples and conformance notes for review and smoke-check workflows

## Canonical runtime path

- Canonical runtime family: `/v1/*`
- Canonical inference path: `POST /v1/chat/completions`

Stage 1 documents the path and the contract vocabulary.
It does not introduce a new runtime implementation in this docs site.

## Proof surface fields

The VEILTHORN proof surface keeps the following fields explicit:

- `claim`
- `supportingEvidence`
- `invalidatingEvidence`
- `verification`
- `replay`
- `operationalStatus`
- `truthBoundary`
- `nextEvidenceRequired`

## Page map

- [Quick start](./quick-start.md)
- [API reference](./api-reference.md)
- [Proof surface](./proof-surface.md)
- [Examples](./examples.md)
- [Conformance](./conformance.md)

## Follow-on plan

Stage 2 remains the follow-on plan.
When that work starts, it should add runtime behavior, enforcement, and deployment evidence instead of expanding the docs layer by implication.
