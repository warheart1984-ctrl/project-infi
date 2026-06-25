# DAR-Z Kernel

DAR-Z is a deterministic execution kernel for the boundary between cognition and
state mutation. It evaluates one canonical `TrajectoryMessage`, projects it into
an `InvariantObject`, applies K32 stability plus LiSCAL, EGL, SDAF, and SSAGL
admissibility filters, emits an append-only audit record, and returns exactly one
`ExecutionDecision`.

## Execution Chain

```text
Omega -> LTS -> T(S) -> OIWL -> Forge_k -> IG_k -> LiSCAL -> EGL -> SDAF -> SSAGL -> SCIL -> SCOL -> Runtime
```

The Rust crate implements the kernel boundary:

```rust
let validator = DefaultKernelValidator::new(KernelPolicy::default());
let decision = validator.evaluate(&message);
```

## Properties

- Determinism: same message and same policy produce the same decision receipt.
- Totality: every message returns `Execute` or `Block`.
- No axis side effects: axes are pure functions over the invariant object.
- Single runtime gate: mutation runtimes must dispatch only from an `Execute`.
- Auditability: every evaluation emits an append-only `ExecutionAudit`.

## AAIS Handshake

DAR-Z interop uses the workspace canonical AAIS reasoning profile and CCS/DZI-1
continuity-evidence handshake:
[`docs/contracts/AAIS_REASONING_PROFILE.md`](../docs/contracts/AAIS_REASONING_PROFILE.md).
Concrete CCS object schemas and fixtures are in
[`docs/contracts/CCS_CORE_SCHEMA.md`](../docs/contracts/CCS_CORE_SCHEMA.md),
[`schemas/ccs_core_objects.v1.json`](../schemas/ccs_core_objects.v1.json), and
[`fixtures/ccs/`](../fixtures/ccs/).

## Voss Binary Runtime

`runtime::voss` is the post-kernel binary runtime adapter. It does not decide
governance. It accepts a completed `ExecutionDecision` and a
`VossCapabilityRequest`.

- `Execute` produces a `BOUND` Voss receipt with `lambda_coupling_id`,
  `scar_id`, `debt_id`, and the kernel `replay_hash`.
- `Block` produces a `REJECTED` receipt and does not execute the binary
  capability.

This mirrors the existing Python Voss/USL model while preserving DAR-Z's pure
validator boundary.

## Sovereign Node Bootstrap

1. Generate node identity: `node_id`, keypair, jurisdiction ID.
2. Load regime: `regime_id` and LiSCAL/EGL/SDAF/SSAGL policy bundle.
3. Initialize audit sink: append-only execution audit storage.
4. Instantiate `DefaultKernelValidator { policy, audit_sink }`.
5. Wire cognition proposals to `TrajectoryMessage`.
6. Route `ExecutionDecision::Execute` into runtime adapters such as Voss.
7. Route `ExecutionDecision::Block` to audit-only handling.
8. Store `(TrajectoryMessage, policy snapshot, decision, replay_hash)` for
   replay verification.
9. Optionally gossip audit digests as evidence, never as external authority.

## Formal Scaffold

The `theories/` directory contains a Coq skeleton matching the Rust shape:

- `Types.v`
- `Axes.v`
- `Kernel.v`
- `Properties.v`
- `K32.v`

`eval_total` and `eval_deterministic` are expressed directly. Policy
monotonicity is represented as an axiom until the concrete policy lattice is
formalized.
