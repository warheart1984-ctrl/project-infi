# CEN-AAES Authority Token Protocol

## Token Types
- `VT`: veto token
- `FT`: freeze token
- `MRT`: mandatory review token
- `RT`: realignment token

## Lifecycle
Tokens are issued with type, scope, transition binding, expiry, and placeholder SHA3-256 signature. CEN validates signature, expiry, scope, transition binding, and replay status before evaluation proceeds.

## Refusals
CEN emits `TOKEN_INVALID_SIGNATURE`, `TOKEN_EXPIRED`, `TOKEN_SCOPE_DENIED`, `TOKEN_TRANSITION_MISMATCH`, or `TOKEN_REPLAYED`.
