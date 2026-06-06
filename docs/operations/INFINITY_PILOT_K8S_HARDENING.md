# Infinity Pilot — K8s Hardening

CISIV stage: **verification**

## Scope

Platform Membrane Helm chart at `deploy/platform/helm/` — NetworkPolicy, Secret-backed API key, ServiceAccount, resource limits.

## Install

```bash
helm upgrade --install platform deploy/platform/helm \
  --set secrets.masterApiKey=<rotated-key> \
  --set env.PLATFORM_REQUIRE_API_KEY=1
```

## Hardening checklist

- [x] NetworkPolicy ingress/egress allowlist
- [x] PLATFORM_MASTER_API_KEY via Secret (not values plaintext)
- [x] ServiceAccount on API deployment
- [x] CPU/memory requests and limits

## Isolation proof

```bash
python scripts/k8s_tenant_isolation_smoke.py
make plat-pilot-k8s-gate
```

Evidence: [PLATFORM_K8S_ISOLATION_PROOF.md](../proof/platform/PLATFORM_K8S_ISOLATION_PROOF.md)
