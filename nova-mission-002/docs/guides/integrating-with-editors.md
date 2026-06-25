# Integrating with Editors

Wrap editor mutations:

```typescript
async function governedApplyDiff(diff: string) {
  const action = { type: "edit", payload: { diff } };
  await governance.validateAction(action);
  const result = await runtime.applyDiff(diff);
  const receipt = await governance.recordReceipt(action, ["editor"]);
  return { result, receipt };
}
```

Cursor / Nemotron adapters belong in an integration layer above the SDK.
