# Platform K8s Isolation Proof

Status: **proven** (logical tenant partition; Helm manifest offline validation)

CISIV stage: **verification**

## Claim

Platform API enforces org-scoped ledger isolation for multi-tenant pilot workloads; Helm chart ships NetworkPolicy + Secret wiring for K8s deploy.

## Reproduction

```bash
python scripts/validate-k8s-helm-manifest.py
python scripts/k8s_tenant_isolation_smoke.py
make plat-pilot-k8s-gate
```

## Evidence

| Check | Artifact |
|-------|----------|
| Helm templates | `deploy/platform/helm/templates/networkpolicy.yaml` |
| Isolation report | `ci-artifacts/k8s_isolation_report.json` |
| Offline tests | `tests/test_k8s_helm_hardening.py` |
