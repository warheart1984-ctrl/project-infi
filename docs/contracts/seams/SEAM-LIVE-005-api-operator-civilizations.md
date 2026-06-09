# 005

## Title

Live probe failure: `GET /api/operator/civilizations`

## Classification

- seam class: `governance_seam`
- boundary: `operator_product_surface`
- severity: `high`
- status: open
- discovery state: reproduced under seam_discovery_stress live probe

## Summary

Live seam discovery recorded a boundary violation during operator-mode stress.

## Detection Capture

- endpoint: `GET /api/operator/civilizations`
- status code: `404`
- latency_ms: `18.0`
- error: `none`

## Law Definition

Operator API routes must be registered and reachable via legacy bridge.

## Closure

- [ ] Fix registered route or handler
- [ ] Regression test added
- [ ] Re-run seam_discovery_stress.py — probe green
