# Unified Runtime Specification Template

Every governed runtime **MUST** be specified using this template. It is the universal schema for runtime definition.

## Template

### 1. Purpose

What this runtime exists to protect or guarantee.

### 2. Invariants

The constitutional invariants this runtime is responsible for enforcing.

### 3. Evidence Requirements

What evidence is required for this runtime to act.

### 4. Authority Model

Who may authorize this runtime's actions and under what conditions.

### 5. Reproducibility Requirements

What must be reproducible and how reproduction is validated.

### 6. Impact Boundaries

What this runtime is allowed to affect and what is out of scope.

### 7. Accountability Chain

Who is accountable for this runtime's decisions and failures.

### 8. Failure Modes

What failures this runtime can produce and how they are detected.

### 9. Receipts Produced

List of all Receipt v2 types this runtime emits.

### 10. Legal State Transitions

The allowed transitions for this runtime's State Objects (see Article XV).

### 11. Remediation Obligations

What must occur when this runtime fails (see Article XIV).

### 12. Closure Conditions

What conditions must be met for a decision or remediation to be closed.

---

## Example — Constitutional Runtime

| Section | Value |
|---------|-------|
| **Purpose** | Evaluate amendment proposals and enforce constitutional legality |
| **Invariants** | No silent constitutional change; amendment lifecycle completeness |
| **Evidence** | Trigger receipt, impact analysis, ratification record |
| **Authority** | Sovereignty Runtime ratifies; Constitutional Runtime evaluates |
| **Reproducibility** | Full amendment receipt chain replayable |
| **Impact** | Constitution text and transition graph only |
| **Accountability** | Constitutional Runtime operator; sovereign ratifier |
| **Failure Modes** | Illegal transition, missing trigger, immutable violation |
| **Receipts** | `Amendment*ReceiptV2` (six stages) |
| **Transitions** | `proposed → evaluated → ratified → implemented → observed → closed` |
| **Remediation** | Divergence Receipt → Arbitration → Remediation with `constitutional_trigger` |
| **Closure** | `AmendmentClosureReceiptV2` after observation confirms behavior |

## Example — Observer Runtime

| Section | Value |
|---------|-------|
| **Purpose** | Independent verification without execution authority |
| **Invariants** | Observer independence; full inspect/replay rights |
| **Evidence** | All receipts, ledger entries, state objects for target |
| **Authority** | None for execution; right to inspect and challenge |
| **Reproducibility** | State reconstruction and transition replay |
| **Impact** | Verification receipts only; no state mutation |
| **Accountability** | Observer identity recorded on verification receipts |
| **Failure Modes** | Divergence, missing receipts, illegal transitions |
| **Receipts** | `ObserverVerificationReceiptV2`, `ObserverDivergenceReceiptV2`, etc. |
| **Transitions** | N/A (read-only) |
| **Remediation** | `ObserverRemediationRequestReceiptV2` on failure |
| **Closure** | `ObserverClosureReceiptV2` when verification succeeds |

**Implementation reference:** Each runtime's Receipt v2 types in `operator_kernel/receipts_v2.py`.
