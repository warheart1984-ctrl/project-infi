# Scaling Validation — AAES-OS Production Baseline v1.0

**Baseline:** `AAES-OS-PRODUCTION-BASELINE-v1.0`  
**Frozen commit:** `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`  
**Status:** HPA ranges frozen; load-test pending-cluster-execution

## Frozen HPA ranges

| Target | Min | Max | CPU target | Memory target |
| --- | --- | --- | --- | --- |
| platform-api | 3 | 10 | 70% | 80% |
| platform-web | 2 | 5 | 75% | 85% |
| ops-console | 1 | 3 | 75% | — |

Source: `k8s/ingress-and-load-balancing.yaml` (checksum frozen).

## PDB floors (availability under disruption)

| Target | minAvailable |
| --- | --- |
| platform-api | 2 |
| platform-web | 1 |

## Validation procedure

```bash
kubectl get hpa -n aaes-os
kubectl describe hpa -n aaes-os
kubectl top pods -n aaes-os   # requires metrics-server

# Optional load generation (operator-chosen tool)
# Expect replica count to rise under sustained CPU/memory pressure, then retract
```

## Pass criteria

1. HPA objects exist with the frozen min/max ranges
2. Under synthetic load, replica count increases within max bounds
3. After load removal, replicas decrease toward min without thrashing indefinitely
4. PDB prevents voluntary disruption below `minAvailable`

## Results log

| Check | Result | Evidence |
| --- | --- | --- |
| HPA ranges in manifest | Pass | ingress-and-load-balancing checksum |
| Live scale-up observed | Pending | `pending-cluster-execution` |
| Live scale-down observed | Pending | `pending-cluster-execution` |

## Truth boundary

Documented HPA configuration is frozen. Observed autoscaling behavior requires metrics-server and a live cluster run.
