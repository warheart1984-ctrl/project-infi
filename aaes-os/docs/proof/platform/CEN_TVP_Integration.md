# CEN-TVP Integration

## Purpose
The Transition Validation Pipeline places CEN at the constitutional boundary.

## Stages
1. `pre_validation`: structural validation.
2. `constitutional_validation`: CEN invariant and token validation.
3. `commit` or `block`: state mutation only after CEN allow.
4. `receipt`: terminal evidence path.

## Guarantee
No transition may commit unless `runTransitionPipeline()` returns `allowed: true` and `committed: true`.
