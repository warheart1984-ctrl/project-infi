# Infinity Pilot SLA Orientation (Non-Binding)

Early adopter pilot service levels — orientation only, not a contractual SLA.

## Scope

Infinity Pilot full stack: Platform Membrane v6, UGR Ledger Bridge v1, AAIS operator surface.

## Targets (pilot)

| Area | Target |
|------|--------|
| Platform API availability | Best-effort business hours; no 24/7 guarantee |
| Planned maintenance | 24h notice when possible |
| Incident response | Critical (ingress down): 4h acknowledge; others: next business day |
| Data export | Sovereign pack + usage CSV on request within 5 business days |

## Exclusions

- Multi-region failover (deferred)
- Guaranteed cross-machine proof latency (UGR-D5)
- Paid marketplace / Stripe billing

## Customer responsibilities

- Rotate `PLATFORM_MASTER_API_KEY` and operator keys
- Run `ledger/verify` before compliance sign-off
- Keep `PLATFORM_WITNESS_REQUIRED=0` unless ops team enables witness quorum deliberately

## Claim posture

Pilot readiness: **proven** with local `stack-pilot-gate`. GA: **proven** as of 2026-06-06 ([INFINITY_PILOT_GA_SIGNOFF.md](../audit/INFINITY_PILOT_GA_SIGNOFF.md)).
