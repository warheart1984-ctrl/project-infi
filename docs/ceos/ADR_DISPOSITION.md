# CEOS — ADR Disposition Rule

**Status:** **declared** (Drive-G-1) — classification rule for post-freeze issues; not a runtime gate.  
**Date:** 2026-07-30  
**Source:** Dar-z Morris → Jon Halstead (evidence-driven architecture)  
**ADR home:** [`../adr/README.md`](../adr/README.md) · registry [`../adr/registry.json`](../adr/registry.json)

---

## Rule

When implementation or conformance testing reveals an issue, **do not reopen constitutional design by default**. Classify the issue into exactly one bucket below (or an ordered escalation).

| Bucket | Use when | Where it lands | Tag |
|--------|----------|----------------|-----|
| **ADR** | Decision among valid implementation options; trade-offs; binding local architecture choice that does not change CIS normative meaning | `docs/adr/` (new ADR via template) | **declared** until ACCEPTED + implemented |
| **Future profile** | Domain- or deployment-specific requirements that specialize CEOS/CIS without rewriting Core | Implementation profile docs under `docs/crk1/release/` (or successor profile registry) | **roadmap** / **declared** |
| **Reference architecture** | Clarifies structure, interfaces, or composition of Kernel / CORI / companions; no new constitutional obligation | `docs/architecture/` + SOCK/RA companions | **declared** |
| **Future specification revision** | **Only if necessary** — genuine normative gap or contradiction in frozen constitutional text that cannot be resolved above | Governed change to CIS Core / CEOS constitutional text (CCR/CCP) | exceptional; remains **declared** until ratified |

---

## Escalation order

1. Can an **ADR** resolve it without changing normative meaning? → ADR.  
2. Else, is it profile-scoped? → **Future profile**.  
3. Else, is it structural/composition only? → **Reference architecture**.  
4. Else, and only then → **Future specification revision** (normative gap).

---

## Evidence required for each bucket

| Bucket | Minimum evidence |
|--------|------------------|
| ADR | Problem statement, options, decision, CIS/SOCK impact, tests or deferred test note |
| Future profile | Profile id, parent freeze pointers, non-redefinition of Core terms |
| Reference architecture | Diagram/spec delta, interface list, no new SHALL on Core |
| Spec revision | Gap report from impl/conformance, CCR/CCP trail, freeze amendment notice |

---

## Explicit non-actions

- Chat agreement alone does not create an ADR or unfreeze CEOS/CIS.  
- An accepted ADR does **not** prove production readiness (see existing ADR README).  
- Do not invent features to “use” a disposition bucket.
