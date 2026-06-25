# CRK-1 Kernel Fuzz-Testing Harness

**Version:** 1.0  
**Purpose:** Stress-test the constitutional runtime with randomized, adversarial, and malformed inputs.

---

## 1. Harness Goals

- Break invariants
- Break continuity
- Break ledger
- Break replay determinism
- Break PIT-band evolution
- Break kernel panic handling
- Break constitutional upgrade logic

If CRK-1 survives this, it is production-grade.

---

## 2. Fuzz Categories

### 2.1 Action Fuzzing

Randomized prompts, diffs, plan structures, action sequences, invalid action types.

### 2.2 Invariant Fuzzing

Random invariant injection, removal, mutation.

### 2.3 Continuity Fuzzing

Random snapshot corruption, diff corruption, replay interruptions.

### 2.4 Ledger Fuzzing

Random receipt reordering, deletion, hash tampering.

### 2.5 PIT-Band Fuzzing

Random PIT activation, evidence values, domain mismatches.

---

## 3. Harness Implementation

See `tools/fuzz/fuzz-harness.ts` at repo root.

```ts
import { nova, governance, continuity } from "nova-sdk"

async function fuzzActions(iterations = 1000) {
  for (let i = 0; i < iterations; i++) {
    const prompt = randomPrompt()
    try {
      await nova.generateCode({ prompt })
    } catch (e) {
      console.log("Action fuzz caught:", e)
    }
  }
}
```

---

## 4. Fuzz Execution Protocol

1. Start kernel in isolated mode
2. Run action fuzz → invariant fuzz → continuity fuzz → ledger fuzz → PIT fuzz
3. Export results
4. Compare against expected invariants

---

## 5. Expected Output

- `fuzz-report.json`
- `continuity-fuzz.log`
- `ledger-fuzz.log`
- `invariant-fuzz.log`

---

## Related

- [CRK-1 Kernel Integrity Test Suite](./CRK-1-KERNEL-INTEGRITY-TEST-SUITE.md)
- [Level 3 Operator Certification](../operator/OPERATOR-LEVEL-3-CERTIFICATION.md)
