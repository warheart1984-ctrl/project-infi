# Invariants

Invariants are non-negotiable rules registered via `governance.requireInvariant()`.

```typescript
{
  id: "no-dangerous-shell",
  description: "Disallow dangerous shell commands.",
  severity: "error",
  check: (state) => !state.prompt?.includes("rm -rf"),
}
```

See [Writing Invariants](../guides/writing-invariants.md).
