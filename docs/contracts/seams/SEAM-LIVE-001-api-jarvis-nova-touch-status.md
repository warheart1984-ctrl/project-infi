# 001

## Title

Live probe failure: `GET /api/jarvis/nova/touch/status`

## Classification

- seam class: `governance_seam`
- boundary: `jarvis_status_farm`
- severity: `medium`
- status: open
- discovery state: reproduced under seam_discovery_stress live probe

## Summary

Live seam discovery recorded a boundary violation during operator-mode stress.

## Detection Capture

- endpoint: `GET /api/jarvis/nova/touch/status`
- status code: `404`
- latency_ms: `11.0`
- error: `none`

## Law Definition

Jarvis status routes declared in stress inventory must return 200 smoke responses.

## Closure

- [ ] Fix registered route or handler
- [ ] Regression test added
- [ ] Re-run seam_discovery_stress.py — probe green
