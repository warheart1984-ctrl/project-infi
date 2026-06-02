# Forensic Triangulation v1 Proof Packet

Claim: Mechanic, Scorpion, and Slingshot diagnostic claims correlate into one `triangulation.v1` ledger per `case_id` with temporal and invariant-overlap edges.

Claim status: **proven** on fixture `tri-demo-001` (single-machine). Jarvis tool route: **deferred** (MECH-CHAT-01).

## 1) Incident / Issue ID

- ID: `TRIANGULATION-V1`
- Title: Forensic Triangulation Ledger MVP
- Scope: `triangulation/` package, fixture, CLI, governance gate

## 2) Verification Evidence

### One-click override command

```bash
make triangulation-gate
python -m pytest tests/test_triangulation.py -q
python -m triangulation correlate --case-id tri-demo-001 --fixture tri-demo-001 --triangulation-root .runtime/triangulation/demo
```

### Claim posture

| Claim | Label |
|---|---|
| Proven invariant_overlap edge on tri-demo-001 | proven |
| Jarvis forensic_triangulation tool route | none_yet |
| Cross-machine replay | none_yet |

## 3) Sign-Off

- claim_label: proven
- why_short: Fixture tri-demo-001 produces proven GOV-CI-03 ↔ fd_flow bridge edge; launch_blocked preserved.
- proof_links:
  - docs/proof/forensics/TRIANGULATION_V1_PROOF.md
  - triangulation/fixtures/tri-demo-001/
  - tests/test_triangulation.py
- override_command: make triangulation-gate
