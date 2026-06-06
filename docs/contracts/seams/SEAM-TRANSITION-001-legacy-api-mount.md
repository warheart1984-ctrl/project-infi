# SEAM-TRANSITION-001 — Legacy API mount

## Title

Flask legacy bridge at `/legacy_api` (governed transition)

## Classification

- seam class: `routing_seam`
- boundary: `workflow_shell_legacy_bridge`
- severity: `low` (governed transition)
- status: closed (governed)
- discovery state: documented in AAIS_STATUS_AUDIT

## Summary

FastAPI workflow shell mounts Flask Jarvis runtime via `LegacyFlaskApiBridge` at `/legacy_api`. This is intentional during Infinity Pilot GA; removal deferred post-GA.

## Law Definition

`/health` MUST report `legacy_api_loaded: true` and `legacy_api_mount_error: null`. Any mount error is an **open** seam.

## Closure

- [x] Health invariant enforced in seam stress + wave6 gate
- [x] Documented in AAIS_CHAT_ROUTING_CONTRACT companion
- [ ] Full WSGI bridge removal (post-GA: PLAT-GA-D2)
