# 021

## Title

Live probe failure: `GET /api/operator/multi-being`

## Classification

- seam class: `governance_seam`
- boundary: `genome_runtime_surface`
- severity: `high`
- status: open
- discovery state: reproduced under seam_discovery_stress live probe

## Summary

Live seam discovery recorded a boundary violation during operator-mode stress.

## Detection Capture

- endpoint: `GET /api/operator/multi-being`
- status code: `404`
- latency_ms: `4.0`
- error: `none`

## Law Definition

Genome-declared surface for multi_being_continuity_runtime must be registered in Flask url_map.

## Closure

- [ ] Fix registered route or handler
- [ ] Regression test added
- [ ] Re-run seam_discovery_stress.py — probe green
