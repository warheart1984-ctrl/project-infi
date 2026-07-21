# Quick Start

Use this page to orient yourself in the VEILTHORN Stage 1 docs spine.

## 1. Open the landing page

Start at [VEILTHORN Stage 1](./index.md) for the canonical route map and the Stage 1 scope.

## 2. Read the canonical path

The documented runtime family is the OpenAI-compatible `/v1/*` surface.
The canonical inference path is `POST /v1/chat/completions`.

## 3. Check the proof surface

Read [Proof surface](./proof-surface.md) to see how VEILTHORN separates:

- the claim being made
- the evidence supporting the claim
- the evidence that would invalidate the claim
- the verification and replay posture

## 4. Review the examples

Open [Examples](./examples.md) for the smallest complete reading path through the docs.

## 5. Confirm conformance

Use [Conformance](./conformance.md) to see what must be true for the Stage 1 docs slice to be considered complete.

## Minimal verification

From `docs-site`, run:

```bash
npm run verify
```

That command rebuilds the docs site and runs the smoke check against the generated HTML pages.

## Stage 1 boundary

If you are looking for runtime execution, enforcement, or deployment, that is Stage 2 work and is intentionally outside this docs spine.
