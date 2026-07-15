# API Reference

This page documents the VEILTHORN Stage 1 reference vocabulary.
It does not define a new runtime implementation in this repository.

## Endpoint family

- Family: `/v1/*`
- Canonical inference path: `POST /v1/chat/completions`

The docs site keeps the runtime family OpenAI-compatible in shape, while Stage 1 stays focused on the reference artifact and its proof surface.

## Documented proof fields

The proof/challenge surface uses the following fields:

| Field | Meaning |
| --- | --- |
| `claim` | The statement being made about the artifact or surface |
| `supportingEvidence` | Evidence that supports the claim |
| `invalidatingEvidence` | Evidence that would challenge or falsify the claim |
| `verification` | How the claim is checked |
| `replay` | How the claim or artifact can be replayed from source |
| `operationalStatus` | Current operational state of the documented surface |
| `truthBoundary` | The limit of what the documentation is actually proving |
| `nextEvidenceRequired` | The next evidence needed to move the claim forward |

## Contract notes

- Stage 1 is documentation-only
- The canonical path is `/v1/chat/completions`
- The API reference is a read model, not a deployment contract
- Stage 2 is where runtime behavior should be introduced and verified

## Related pages

- [VEILTHORN Stage 1](./index.md)
- [Proof surface](./proof-surface.md)
- [Conformance](./conformance.md)
