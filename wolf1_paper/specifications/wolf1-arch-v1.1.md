# WOLF-1 Architecture Specification v1.1.0

**Requirement:** REQ-WOLF1-ARCH-001  
**Source:** `src/wolf1_v1.1.md`  
**ADR:** ADR-0001-wolf1-v11-constitutional-extensions

## Scope

Constitutional architecture for WOLF-1 governed compute node in HEO/Lagrange orbit.

## Mandatory sections

1. Mission context — governance non-optional, cognition optional
2. Four-layer stack (physical, platform, cognitive governance, cognitive tenant)
3. Twelve invariants across six axes
4. Power/propulsion controller mediated by CAS
5. Governed cognitive run sequence with epistemic receipts
6. Fault taxonomy and graded safe-mode S0–S3
7. LLM tenancy — proposals only
8. Anomaly discovery framework
9. Constitutional evolution protocol M0–M4

## Validation

- CTS `cts/run_all.sh` must pass before build
- Build receipt with SHA-256 of PDF and HTML outputs
