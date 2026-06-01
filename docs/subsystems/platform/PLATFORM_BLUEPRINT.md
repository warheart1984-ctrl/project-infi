# Platform Membrane Blueprint

## Canonical Definition

The Platform Membrane is the **multi-tenant SaaS ingress** that unifies identity, jobs, artifacts, and audit across governed subsystems (Mechanic, Forgekeeper, Slingshot, Lab Console, AI Factory) without replacing Jarvis/Nova cognition authority.

## Purpose

Convert five constitutional **organs** into one **operable service**: single API boundary, org-scoped RBAC, global job vocabulary, federated artifact index, operator console, and cross-machine proof promotion.

## Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

The platform membrane cannot bypass MA-13 (Stage 2 Copilot Doctrine) or subsystem constitutional boundaries.

## MA-13 Guards At The Membrane

| Class | Platform must not |
|-------|-------------------|
| I — Usurpation | Invent operator goals or auto-approve Stage 3 actuation |
| II — Distortion | Drop subsystem constraints when routing jobs |
| III — Leakage | Expose cross-org artifacts or bypass audit on job dispatch |

## Components

| Component | Responsibility |
|-----------|----------------|
| **Identity** | Orgs, principals, API keys (hashed), RBAC |
| **Job orchestrator** | `platform_job.v1` registry, Redis queue, subsystem adapters |
| **Artifact index** | Federated refs + lineage (blobs stay in subsystem paths v1) |
| **Audit** | Append-only trail tied to `principal_id` |
| **Ingress API** | FastAPI on port 8090 (default) |

## Non-Goals (v1)

- Jarvis/Nova cognition in `platform/`
- OIDC/SSO (debt PLAT-D8)
- Auto-apply or raw Stage 3 through platform routes
- Moving all blobs to S3 (index-first; optional copy)
- Replacing subsystem engines

## Failsafe

- Default: queue job → adapter runs subsystem in governed dry-run/safe modes
- Cross-org reads denied at index and API layers
- Artifact purge requires explicit operator confirm API
- Raw apply remains blocked in Mechanic paths

## Related

- [PLATFORM_API_CONTRACT.md](./PLATFORM_API_CONTRACT.md)
- [OPERATIONAL_RUNBOOK.md](./OPERATIONAL_RUNBOOK.md)
- [../../runtime/PLATFORM_MEMBRANE.md](../../runtime/PLATFORM_MEMBRANE.md)
