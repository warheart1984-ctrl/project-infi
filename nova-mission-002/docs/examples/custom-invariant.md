# Custom Invariant

Add to `config/nova.config.ts`:

```typescript
{
  id: "no-eval",
  description: "Do not use eval()",
  severity: "error",
  check: (state) => !state.code?.includes("eval("),
}
```

Run `nova invariants` to verify registration.
