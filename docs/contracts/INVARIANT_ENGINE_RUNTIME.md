# Invariant Engine Runtime Contract

Status: **active contract**

## Runtime Surfaces

- `InvariantEngine.validate_bridge_packet` — fail-closed on cognitive bridge ingress
- `validate_realtime_event_prediction` — advisory on predictor output
- Nova comparison via `invariant_engine_organ` on companion turns (read-only attestation)

## Governance IR compiler stack

Law is snapshotted as **Governance IR** (`docs/contracts/GOVERNANCE_IR.md`) and lowered by the invariant compiler (`src/invariant_compiler.py`).

| Stage | Entry | Delegates to InvariantEngine |
|-------|-------|------------------------------|
| Ingress | `apply_ingress_plan` | `validate_bridge_packet` |
| Checkpoint | `run_checkpoint_validators` | same + envelope/temperature checks |
| Admission | `run_admission_checks` | same |

Decode-time execution (Approach 2): `src/decode_governance_executor.py` → `execute_with_decode_governance`.

Full artifact schemas: `docs/contracts/INVARIANT_DECODE_GOVERNANCE.md`.

## Fail-closed

- Compiler errors (`InvariantCompilerError`, `GovernanceIRValidationError`) → bridge BLOCK.
- Ingress/admission `allows: false` → BLOCK.
- Nova organ has no mask or execution authority.

## Scope

Math layer is complete; runtime wiring extends bridge ingress, UGR LLM lane, and chat finalize admission through IR-derived bundles.
