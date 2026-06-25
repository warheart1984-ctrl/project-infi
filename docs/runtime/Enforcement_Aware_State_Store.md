# Enforcement-Aware State Store

## Contract
The state store is mutated only through CEN `allow()` or `execute()` when the decision verdict is `ALLOW`.

## Current MVP
CEN uses an in-memory map keyed by transition ID. TVP delegates commits to CEN and never writes state directly.
