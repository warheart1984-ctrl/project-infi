# Writing Invariants

How to extend the constitutional codex without breaking K-∞.

## Rules

1. **Every new invariant must serve K-∞** — if reality cannot recalibrate future judgment, reject it
2. **Invariants constrain; they do not describe** — behavior docs belong elsewhere
3. **Map to enforcement** — every invariant needs a test, receipt, or runtime check
4. **No orphan invariants** — link to CK-1, CRK-1, CE-1, or CLG-1 layer

## Process

### 1. State the failure mode

What happens if this invariant is violated? Which future steward loses corrigibility?

### 2. Choose a section

| Section | When |
|---------|------|
| CK-1 | Breaks minimal kernel |
| G-* | Governance / GRR |
| C-* | Calibration / CE-1 |
| L-* | Lineage / CLG-1 |
| S-* | Steward conduct |

### 3. Add to codex

Edit:

- [`docs/continuity-os/invariants/book-of-invariants.md`](../continuity-os/invariants/book-of-invariants.md)
- [`docs/crk1/crk1_invariants.yaml`](../crk1/crk1_invariants.yaml)

### 4. Implement enforcement

- Runtime assertion in `src/crk1/`
- Red-team attack if insulation-related
- Test in `tests/crk1/`

### 5. Kernel challenge (KΩ)

New invariants affecting the kernel must pass [Mission #004](../continuity-os/missions/mission-004.md) kernel challenge loop.

## IDC — Invariant Discovery Contract

When unexplained continuity failure occurs, IDC may **propose** new invariants — never auto-ratify.

Spec: [`IDC-INVARIANT-DISCOVERY-CONTRACT`](../crk1/IDC-INVARIANT-DISCOVERY-CONTRACT.md)

## Example

```
L-5  Calibration events must reference at least one reality channel.
```

Enforcement: CLG-1 ingest requires `observed_via` edge to RealityChannel node.
