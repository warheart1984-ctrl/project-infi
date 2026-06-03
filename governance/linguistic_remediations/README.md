# Linguistic Remediation Playbooks

Wave 9 operator-actionable artifacts derived from [linguistic_drift_report.v1.json](../linguistic_drift_report.v1.json).

## Generate

```bash
python tools/governance/generate_linguistic_remediations.py --min-band medium
make linguistic-remediation-gate
```

## Policy

- Playbooks are **draft only** — never auto-applied
- `mp_ling_draft` actions include delta JSON under `schemas/deltas/` when `--write-deltas` is used
- Review before `apply_linguistic_mutation.py --apply`

Contract: [docs/contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md](../../docs/contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md)
