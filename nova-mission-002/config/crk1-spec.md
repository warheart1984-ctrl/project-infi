# CRK-1 Constitutional Contract v1.0

## 1. Purpose

CRK-1 defines the lawful substrate for agentic cognition. All agents must operate within:

- continuity
- invariants
- traceability
- reproducibility
- governance receipts

## 2. Lawful Action

Every agent action must:

1. Be validated by the invariant engine
2. Produce a governance receipt
3. Update the continuity substrate
4. Be reversible (via replay)
5. Be traceable

## 3. Invariant Engine

An invariant is a non-negotiable rule:

```
Invariant {
  id: string
  description: string
  check(state): boolean
  severity: "error" | "warn"
}
```

## 4. Pattern Ledger

Every action is logged with:

- action type
- payload
- continuity hash
- invariant checks
- timestamp
- cryptographic chain: h_i = H(R_i || h_{i-1})

## 5. Continuity Substrate

The substrate maintains:

- snapshots
- diffs
- replay logs
- continuity hashes

## 6. Receipts

Every action produces a receipt:

```
GovernanceReceipt {
  id
  timestamp
  action
  invariantsChecked
  continuityHash
  ledgerHash
}
```

## 7. Reproducibility

Any external observer must be able to:

- replay the agent's reasoning
- verify invariants
- confirm continuity

This is the core of founder-independent reproduction.

## 8. Constitutional Rules

- **No silent actions** — every action produces a receipt
- **No ungoverned code generation** — all generation passes invariants
- **No unvalidated transitions** — L(S, A) must hold before T(S, A)
