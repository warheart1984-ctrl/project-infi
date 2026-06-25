# Building Tools

Import the SDK and subscribe to lifecycle events:

```typescript
import { nova, events, governance } from "nova-sdk";

events.onReceipt((r) => console.log("Receipt:", r.id));
events.onViolation((v) => console.error("Violation:", v.invariantId));
```

Wrap editor actions with `governance.validateAction` before execution.
