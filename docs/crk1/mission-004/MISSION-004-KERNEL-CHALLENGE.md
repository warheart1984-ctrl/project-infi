# Mission #004 — Invariant Discovery & Kernel Challenge

**Question:** Are K0–K_n still adequate with respect to reality?

## Artifacts

| Artifact | Module | Role |
|----------|--------|------|
| `InvariantPerformanceRecord` | `kernel_challenge_loop.py` | Per-invariant reality feedback |
| `KernelChallengeReceipt` (KCR) | `kernel_challenge_loop.py` | Forces review when K_i fails systematically |
| `InvariantDiscoveryProposal` | `invariant_discovery_contract.py` | Proposes K_{n+1} from unexplained degradation |
| `KernelChallengeLoop` | `kernel_challenge_loop.py` | Accumulation → threshold → docket |

## Lifecycle

1. **Accumulation** — GRRs link to decisive invariants; outcomes update `InvariantPerformanceRecord`.
2. **Thresholding** — failure rate crosses governance threshold → emit KCR.
3. **Governance review** — KCR enters Kernel Review Docket (requires GRRs, RCL metrics, IDC proposals).
4. **Constitutional response** — refine, narrow, broaden, split, or deprecate K_i; new epoch + GRR.

## Distinction

- **Kernel compliance** — did the action satisfy K0–K15 as implemented? (receipts, engine)
- **Kernel validity** — are K0–K15 still adequate? (only testable by consequence exposure)

## Meta-invariant

**KΩ** — No layer may be consequence-immune. See `crk1_invariants.yaml`.

## Seal

No separate seal in M4; KCR emission + governed response is the completion criterion.
