---
title: Nova Studio
description: Operator shell that renders proof surfaces, the constitutional evidence graph, and governed runtime panels.
---

# Nova Studio

Nova Studio is the operator-facing shell that renders proof surfaces, the Constitutional Evidence Graph, and the governed runtime panels.
It points at any proof-surface backend with a catalog URL, or falls back to the local registry for offline use.

## Package source

- [nova-studio/src/components/StudioApp.tsx](../../../nova-studio/src/components/StudioApp.tsx)
- [nova-studio/src/proofSurfaces.ts](../../../nova-studio/src/proofSurfaces.ts)
- [nova-studio/scripts/smoke.ts](../../../nova-studio/scripts/smoke.ts)

## Runtime contract

- Render the proof-surface catalog from a live operator backend or the local registry
- Load the Constitutional Evidence Graph summary rooted in the release receipt
- Offer catalog control (URL entry, local-registry switch, reset to default)
- Surface the SovereignX Router claim, governance, ledger, and runtime panels
- Keep the operator shell in lockstep with the public docs claim boundary

## Verification

- `corepack pnpm --filter @aaes-os/nova-studio verify` builds the production bundle and runs the smoke check
- Smoke asserts the dist root renders, a JavaScript bundle exists, and replay coverage passes for the local registry

## Related pages

- [Live Surfaces](./live-surfaces.md)
- [Overview](../overview.md)
- [Sovereign IDE](../visualizer/sovereign-ide.md)
