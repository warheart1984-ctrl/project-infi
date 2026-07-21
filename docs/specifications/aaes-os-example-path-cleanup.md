# AAES-OS Example Path Cleanup Slice

Status: Documentation-first, sprint 4

## What this slice is

This slice is the next backlog item after the governance traceability slice.
It cleans up the example application path so contributors can move through the AAES-OS docs in a simple, linear order without implying any new runtime behavior.

## In scope

- A clean contributor reading order for the AAES-OS spec set
- The example application path from the first implementation slice through API reference stabilization and governance traceability
- Clear next-step guidance for where examples and follow-on docs should live
- Cleanup notes that avoid implying unimplemented runtime or service behavior

## Out of scope

- New runtime services or API surface area
- Enterprise, federation, or research expansion
- Runtime changes disguised as documentation cleanup
- Example paths that suggest a feature is complete when it is still only documented

## Traceability matrix

| Source spec | What it anchors | Example-path cleanup work |
| --- | --- | --- |
| AAES-OS Engineering Handbook | Contributor baseline and platform posture | Keep the example path aligned to the stable docs-first reading order |
| AAES-OS Engineering Specification | API rules and module boundaries | Keep the example path from inventing new interfaces or behaviors |
| AAES-OS Engineering Standards | Repository requirements and docs hygiene | Keep the path clean, linear, and synchronized across source docs and docs-site mirrors |
| AAES-OS Governance Specification | Evidence model and approval workflow | Keep the path from implying governance or runtime claims that are not yet proven |
| AAES-OS Product Roadmap | Future sequencing and milestone boundaries | Keep the path bounded to the current sprint-sized cleanup work |

## What the cleanup requires

1. Start with the first implementation slice.
2. Proceed to API reference stabilization.
3. Then read governance traceability.
4. Stop before later roadmap milestones or broader runtime claims.
5. Tell contributors where to go next without implying the implementation is done.

## Example application path

1. Open the first implementation slice as the entry point.
2. Read the API reference stabilization slice to keep the interface language explicit.
3. Read the governance traceability slice to keep new claims tied to evidence.
4. Use the cleaned-up path to choose the next backlog item instead of widening scope.
5. Stop before enterprise, federation, or research topics unless a later sprint explicitly adds them.

## Checklist

- [x] The prior slices already exist
- [x] The example application path stays documentation-first
- [x] The cleanup is sprint-sized and scoped to docs navigation
- [x] The path avoids runtime claims that are not implemented

## What comes next

After this slice, the backlog should move from docs sequencing into any remaining documentation gaps or implementation work that has a concrete owner and scope.
