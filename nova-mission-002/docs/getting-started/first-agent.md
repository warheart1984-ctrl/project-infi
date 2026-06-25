# First Agent

```typescript
import { nova, governance } from "nova-sdk";
import { invariants } from "../config/nova.config";

async function main() {
  for (const inv of invariants) {
    await governance.requireInvariant(inv);
  }

  const result = await nova.generateCode({
    prompt: "Implement a function to sort an array of numbers.",
  });

  console.log(result.code);
  console.log("Receipts:", result.receipts);
}

main();
```

Every generation produces governance receipts with continuity hashes.
