# Runtime Audit Records — AAES-OS Production Baseline v1.0

**Baseline:** `AAES-OS-PRODUCTION-BASELINE-v1.0`  
**Frozen commit:** `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`  
**Status:** Audit surface defined; live records pending

## Audit surface (operational)

| Record type | Source | Purpose |
| --- | --- | --- |
| Deploy apply log | `kubectl apply` stdout + event timeline | Prove what was applied |
| Image digests running | `kubectl get pods -o jsonpath=...ImageID` | Prove immutable pins |
| Probe outcomes | kubelet events + `/health` `/ready` curls | Prove liveness/readiness |
| HPA decisions | `kubectl describe hpa` | Prove scaling behavior |
| NetworkPolicy evaluation | deny/allow connectivity tests | Prove zero-trust posture |
| CI provenance | Actions run + Trivy SARIF | Prove build/security lineage |
| Constitutional linkage | RunLedger / evidence-receipts / release receipt | Bridge ops → governance |

## Linkage to governance packages

Operational audits SHOULD reference (when available):

- `packages/runledger` — run and span records
- `packages/evidence-receipts` — receipt emission
- `release/constitutional-release-receipt.json` — release-level receipt
- `docs/release/production-hardening/` — package surface evidence

## Minimum audit packet for independent reproduction

```json
{
  "baselineId": "AAES-OS-PRODUCTION-BASELINE-v1.0",
  "frozenCommit": "7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d",
  "appliedAt": "<ISO-8601>",
  "operator": "<steward-id>",
  "clusterContext": "<context-name-redacted-as-needed>",
  "imageDigests": {},
  "healthSnapshot": {},
  "hpaSnapshot": {},
  "networkPolicyTests": {},
  "ciRunUrl": null,
  "notes": []
}
```

Attach completed packets beside this file as `runtime-audit-<ISO-date>.json`.

## Results log

| Record | Result |
| --- | --- |
| Audit schema defined | Pass |
| First live audit packet | Pending |

## Truth boundary

Defining the audit surface is necessary for stewardship. It is not a substitute for emitted runtime audit records from a real deployment.
