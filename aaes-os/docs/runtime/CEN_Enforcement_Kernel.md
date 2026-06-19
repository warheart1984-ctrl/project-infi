# CEN Enforcement Kernel

The Constitutional Enforcement Node is an enforcement-first runtime primitive for AAES OS.

## Boundary
CEN sits before state mutation. A transition cannot commit until CEN validates corridor capability and invariant conformance.

## Decisions
The kernel emits:

- `ALLOW` with reason `ALLOWED`;
- `DENY` with reason `CAPABILITY_DENIED`;
- `DENY` with reason `INVARIANT_VIOLATION`;
- `DENY` with reason `INVALID_TRANSITION`.

## Receipts
Each receipt includes:

- transition ID and type;
- actor;
- verdict and reason;
- invariant evaluations;
- MRI snapshot hash;
- payload hash;
- previous receipt hash;
- receipt hash.

## Operator Surface
`GET /cen/demo` returns a deterministic CEN result for console visibility.
