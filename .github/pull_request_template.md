## Summary

<!-- What changed and why (1–3 sentences). -->

## Claim posture

- [ ] Significant claims labeled: `asserted` / `proven` / `rejected`
- [ ] Proof artifact linked (trust bundle, gate output, or proof doc path)
- [ ] No unproven release-readiness claims

## Change-of-reality (when behavior changes)

- [ ] Contract / blueprint docs updated
- [ ] Tests or gate command updated
- [ ] Fail-safe or operational docs updated if operator-facing

## Verification

```bash
# List commands run locally:
```

## Requirement & Traceability

**Primary requirement ID(s):**
- REQ-XXXX

**Traceability impact:**
- **ADR:** Does this add/change an ADR? Link:
- **Reference Implementation:** Files / modules touched:
- **CTS:** Tests added/updated (IDs or paths):
- **Evidence Ledger:** Evidence entries or scripts affected:
- **Benchmark/Replication:** Benchmarks added/updated (if applicable):

> Every normative requirement must maintain a complete, machine-verifiable traceability chain:
> **Requirement → ADR → Reference Implementation → CTS → Evidence Ledger → Benchmark/Replication** (where applicable)

For `wolf1_paper/` changes, run:

```bash
cd wolf1_paper
pip install -r requirements.txt
bash scripts/enforce_governance.sh
```

## Debt

<!-- Link any new or updated debt register entries, or write "none". -->
