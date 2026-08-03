# CEF v1.0 Stewardship Dashboard (Prometheus / Grafana)

**Status:** Specified — implement in Phase 5  
**Parent:** [../STEWARDSHIP_PROTOCOL_V1.md](../STEWARDSHIP_PROTOCOL_V1.md)

## 1. Metrics to expose (Prometheus)

### Evidence metrics

```text
cef_evidence_total{type="OEL|CREC|CEL|Security|ModelEval"}
cef_evidence_verification_failed_total
cef_evidence_replay_errors_total
```

### Certificate metrics

```text
cef_certificate_total{status="DRAFT|ACTIVE|REVOKED|HISTORICAL"}
cef_certificate_promotions_total
cef_certificate_revocations_total
```

### Gate metrics

```text
cef_gate_security_failed_total
cef_gate_conformance_failed_total
cef_gate_policy_failed_total
```

### Stewardship metrics

```text
cef_stewardship_renewal_pending_total
cef_stewardship_active_total
```

Machine-readable list: [prometheus-metrics.yaml](./prometheus-metrics.yaml)

## 2. Grafana dashboards

### Dashboard 1 — Evidence Health

- Evidence by type: bar chart of `cef_evidence_total` by `type`
- Verification failures over time: `cef_evidence_verification_failed_total`
- Replay errors: `cef_evidence_replay_errors_total`

### Dashboard 2 — Certificates and promotion

- Certificates by status: pie/bar of `cef_certificate_total` by `status`
- Promotion rate: `cef_certificate_promotions_total`
- Revocation events: `cef_certificate_revocations_total`

### Dashboard 3 — Gates and stewardship

- Gate failures: stacked series of security / conformance / policy fail totals
- Stewardship states: `cef_stewardship_active_total`, `cef_stewardship_renewal_pending_total`
- Drill-down table: recent certificates with status, profile, last gate failure

Import stubs may live under `infra/grafana/` when Phase 5 lands.
