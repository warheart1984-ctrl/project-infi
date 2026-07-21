# AAIS Routing Analytics

This page shows live routing analytics for AAIS -> SovereignX -> Engine decisions.

## Live Runtime View

```ts
import { getAAISRoutingStats } from '@aaes-os/aais';

export default async function RoutingAnalytics() {
  const stats = await getAAISRoutingStats();

  return stats.byCapability.map((entry) => ({
    capability: entry.capabilityName,
    totalInvocations: entry.total,
    modelSplit: entry.byModel,
    overrides: entry.overrides,
    hintsUsed: entry.hintsUsed,
    heuristicFallbacks: entry.heuristicFallbacks,
  }));
}
```

## What It Tracks

- How often each capability is invoked
- Which model each capability routes to
- How often overrides are used
- How often AAIS hints are used
- How often heuristic fallbacks are needed

## Canonical Counters

- `total` counts all routing events for a capability.
- `byModel` splits traffic between `qwen-3b` and `qwen-7b`.
- `overrides` counts user-selected model overrides.
- `hintsUsed` counts AAIS-directed routing events.
- `heuristicFallbacks` counts prompt-size fallback decisions.
