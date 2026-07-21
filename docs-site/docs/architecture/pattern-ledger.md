# Pattern Ledger

The `PatternLedger` in `@aaes-os/aaes-governance` clusters recurring faults by code and invariant.

## Usage with CodingRouter

```ts
import { PatternLedger } from '@aaes-os/aaes-governance';
import { CodingRouter, loadCodingPolicyPack } from '@aaes-os/governed-runtime';

const ledger = new PatternLedger();
const router = new CodingRouter(backends, loadCodingPolicyPack(), ledger);
```

Every coding action can be correlated with fault patterns for drift detection and governance analytics.

## API

- `ingestFault(event)` — record a fault and update pattern recurrence
- `getAll()` — all pattern records
- `getTopRecurring(limit)` — highest-recurrence patterns
