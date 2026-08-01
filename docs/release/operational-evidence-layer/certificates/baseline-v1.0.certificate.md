# Baseline Certificate v1.0 (DRAFT)

Formal CEF certificate structure for AAES-OS Production Baseline v1.0.
Remains DRAFT until all gates pass.

```yaml
certificateId: cert-baseline-v1.0
status: DRAFT
version: 1.0.0
profile: OEL
evidenceRef: evidence-baseline-v1.0
authority:
  carId: car-ops-001
  actorId: ops-approver-001
verification:
  integrity: pending
  completeness: pending
  security:
    sbom: pending
    vulnerabilityScan: pending
    supplyChain: pending
  conformanceTests:
    passed: 0
    total: 0
  policyValidation:
    netpol: pending
    rbac: pending
    securityContext: pending
replay:
  instructions: "Replay instructions will be populated once evidence gates pass."
audit:
  visibility: internal
  disclosure: []
promotion:
  decision: HOLD
  signature: null
  timestamp: null
stewardship:
  state: unpromoted
```

## Notes

- Certificate remains DRAFT/HOLD until all gates are satisfied.
- Prevents “greenwashing” deployments.
- Ensures constitutional integrity.

Machine copy: [baseline-v1.0.certificate.yaml](./baseline-v1.0.certificate.yaml)  
Evidence binding: Production Baseline [../production-baseline/aaes-os-v1.0/INDEX.md](../production-baseline/aaes-os-v1.0/INDEX.md) (path from cef/examples — prefer OEL certificates folder).
