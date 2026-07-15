# Kubernetes and Service Mesh Generation Blueprint

This document defines inputs for generated manifests. It is not a production manifest set: immutable image digests, secrets, storage classes, domains, certificates, resource measurements, and environment overlays must be supplied by release engineering.

| Workload | Kind | Replicas | Port | Required configuration |
|---|---|---:|---:|---|
| `ciems-kernel` | Deployment + ClusterIP Service | 3 | 8080 | `CONSTITUTION_PATH`, `GOVERNANCE_PROFILE`; constitution ConfigMap mounted read-only |
| `isl-compiler` | Deployment + ClusterIP Service | 2 | 8090 | program-registry and USS read endpoints |
| `orchestration-engine` | Deployment + ClusterIP Service | 3 | 8100 | CIEMS authorization and adapter-manager endpoints |
| `adapter-manager` | Deployment + ClusterIP Service | 2 | 8110 | registry endpoint and candidate allowlist |
| `adapter-instance-<substrate>` | Deployment + ClusterIP + HPA | measured | contract-defined | one workload identity and egress policy per substrate |
| `uss-graph-engine` | StatefulSet + headless/ClusterIP Services | 3 | 8120 | PVC template, backups, quorum disruption budget |
| `api-gateway` | Deployment + LoadBalancer/Gateway | 2 | 80/443 | TLS termination, OAuth/JWT validation, rate limits |

Every pod receives a mesh sidecar, readiness/liveness/startup probes, resource requests and limits, a non-root read-only security context, topology spread constraints, and a PodDisruptionBudget. Production generators must replace tags such as `latest` with signed immutable digests.

## Mesh authorization

- Mesh-wide mTLS mode is `STRICT`; default authorization is deny.
- `interface.api-gateway` may call CIEMS public gates and read-only USS projections.
- `planning.isl-compiler` may read USS evidence and the substrate registry; it submits plans to CIEMS.
- `governance.ciems-kernel` alone approves intents, plans, executions, evidence, and USS writes.
- `orchestration.engine` may call adapter workloads only with a valid execution token; it cannot call raw substrates.
- `substrate.adapter.*` may call only its contract-bound `substrate.raw.*` destination.
- `storage.uss.*` accepts writes only from CIEMS. Gateway access is restricted to query/replay projections.
- Circuit breakers, retry budgets, concurrency limits, and rate limits are generated per substrate risk profile; mutation retries require idempotency keys.

## Generation acceptance

Generated overlays fail validation unless they include NetworkPolicies, mesh AuthorizationPolicies, service accounts with least-privilege RBAC, encrypted secret references, signed image digests, probes, resources, disruption budgets, autoscaling bounds, backup/restore configuration, audit export, and a conformance test proving prohibited paths are denied.
