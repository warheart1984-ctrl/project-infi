# Writing Invariants

1. Choose a unique `id`
2. Write a `check(state)` function
3. Set `severity` to `"error"` (block) or `"warn"` (log)
4. Register with `governance.requireInvariant()`

Test by prompting actions that should fail.
