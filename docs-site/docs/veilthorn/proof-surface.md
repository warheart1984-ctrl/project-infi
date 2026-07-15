# Proof Surface

VEILTHORN Stage 1 keeps the proof/challenge surface explicit so the docs do not overclaim.

## Surface fields

| Field | Purpose |
| --- | --- |
| `claim` | States the exact thing the documentation is asserting |
| `supportingEvidence` | Names the artifacts that support the claim |
| `invalidatingEvidence` | Names the evidence that would challenge the claim |
| `verification` | Describes how a reader or checker can verify the claim |
| `replay` | Describes the replay path from source to artifact |
| `operationalStatus` | Records whether the surface is docs-only, reference-only, or live |
| `truthBoundary` | States what the surface does not prove |
| `nextEvidenceRequired` | Lists what evidence is needed for the next step |

## Canonical example

```json
{
  "claim": "VEILTHORN Stage 1 documents the reference surface for the governed runtime family.",
  "supportingEvidence": [
    "docs/veilthorn/index.md",
    "docs/veilthorn/quick-start.md",
    "docs/veilthorn/api-reference.md"
  ],
  "invalidatingEvidence": [
    "A missing docs build",
    "A smoke test failure",
    "A claim that Stage 2 is already implemented"
  ],
  "verification": "Run the docs build and smoke test, then review the generated HTML pages.",
  "replay": "Rebuild the docs site from source and compare the generated docs output.",
  "operationalStatus": "docs-only",
  "truthBoundary": "This page does not prove a live Stage 2 runtime.",
  "nextEvidenceRequired": [
    "Stage 2 runtime implementation",
    "Operational verification evidence",
    "Deployment evidence"
  ]
}
```

## Canonical path reminder

The canonical inference path documented for this family is `POST /v1/chat/completions`.

## Why this matters

Keeping these fields visible makes it harder to blur documentation, evidence, and runtime behavior into one claim.

