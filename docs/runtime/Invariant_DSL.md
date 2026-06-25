# Invariant DSL

AAES OS supports a minimum viable invariant DSL for CEN admission checks.

## Syntax
```text
require <dimension> >= <floor>
```

## Dimensions
- `continuity`
- `governance`
- `memory`
- `coordination`
- `confidence`

## Example
```text
require governance >= 70
```

The compiler maps this to an invariant ID:

```text
idsl:governance:min:70
```

The compiled invariant evaluates the proposed transition payload first, then falls back to the MRI snapshot in the enforcement context.
