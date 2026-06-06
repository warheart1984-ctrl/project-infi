# Production GA Deploy Sign-Off — 2026-06-06

CISIV stage: **verification**

## Scope

Infinity Pilot production deploy path: compose smoke, stack-pilot-gate, production-hardening-gate, K8s isolation proof.

## Claims matrix

| # | Claim | Label | Evidence |
|---|-------|-------|----------|
| 1 | Production hardening invariants | proven | `make production-hardening-gate` |
| 2 | Pilot local compose smoke | proven | `scripts/pilot_compose_smoke.py --local` |
| 3 | Full stack pilot gate | proven | `make stack-pilot-gate` |
| 4 | K8s Helm manifest hardening | proven | `make plat-pilot-k8s-gate` |
| 5 | Tenant isolation smoke | proven | `ci-artifacts/k8s_isolation_report.json` |

## Reproduction

```bash
python .github/scripts/check-production-hardening.py
python scripts/pilot_compose_smoke.py --local
make stack-pilot-gate
make plat-pilot-k8s-gate
python scripts/k8s_tenant_isolation_smoke.py
```

## Related

- [INFINITY_PILOT_GA_SIGNOFF.md](./INFINITY_PILOT_GA_SIGNOFF.md)
- [2026-06-06-production-ga-deploy.md](../trust_bundles/2026-06-06-production-ga-deploy.md)
