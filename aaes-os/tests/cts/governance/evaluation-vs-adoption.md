# CTS-GOV-001 — Governance Evaluates; Evidence Adopts

**Requirement:** REQ-GOV-001
**Policy:** GOV-POL-001

## Assertion

Governance processes evaluate proposals; evidence artifacts justify adoption. Neither domain may substitute for the other.

## Checks

1. **Registry** — `GOV-POL-001` exists in `registries/governance.yaml` and links to `REQ-GOV-001`.
2. **Constitution** — Article II principle 8 present in `constitution/AAES-OS-Constitution.md`.
3. **Charter** — Evaluation vs Adoption section present in `constitution/Governance-Charter.md`.
4. **Evidence Standard** — Foundational Rule present in `constitution/Evidence-Standard.md`.
5. **PR discipline** (manual until CI wired) — core changes cite ADR + evidence artifact IDs; merge blocked if evidence is missing or contradictory.

## Pass criteria

All registry and document checks pass. PR discipline is advisory until CTS runner enforces it in CI.
