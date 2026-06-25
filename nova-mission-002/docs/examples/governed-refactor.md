# Governed Refactor

```typescript
const result = await nova.refactor({
  file: "src/utils.ts",
  instructions: "Extract helper functions for clarity",
});
console.log(result.diff, result.receipts);
```
