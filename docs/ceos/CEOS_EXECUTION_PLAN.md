# CEOS — Execution Plan (post-freeze)

**Status:** **declared** (Drive-G-1) — binding near-term work order; track tags below are evidence-bound.  
**Date:** 2026-07-30  
**Freeze companion:** [`CEOS_V1_FREEZE.md`](./CEOS_V1_FREEZE.md)  
**Disposition:** [`ADR_DISPOSITION.md`](./ADR_DISPOSITION.md)

Constitutional design is complete for the near term. Work shifts to **execution**. Do not expand architecture ahead of these tracks.

---

## Execution tracks

| # | Track | Intent | Present evidence (paths) | Status |
|---|-------|--------|--------------------------|--------|
| 1 | Finalize Constitutional Specification | Stable normative text for implementors | CIS Core artifacts under `docs/crk1/release/` (`CIS_CORE_*`, hierarchy, traceability) | **partial** — baseline frozen; “finalize for execution” = close remaining implementor gaps without redesign |
| 2 | Finalize Reference Architecture + ADR framework | Architecture + decision trail for evidence-driven issues | `docs/architecture/`, `docs/adr/` (template, registry, accepted ADRs) | **partial** — ADR framework exists; CEOS disposition rule added |
| 3 | Build Constitutional Kernel + **CORI Alpha** reference runtime | Minimal runtime that proves identity → evidence → state → receipt → replay → conformance | SOCK spec: `docs/specifications/aaes-os-constitutional-kernel-specification.md`; CORI docs: `docs/crk1/release/CORI_ALPHA_*`; runtime dir: `.runtime/cori-alpha/`; tests: `tests/release/cori-alpha-proof.test.ts` | Kernel: **declared** / **skeleton–partial** packages; CORI Alpha: **partial** (proof plan + artifacts; not milestone-complete) |
| 4 | Develop executable conformance suite | Objective, reproducible suite from traceability | Spec/freeze: `CIS_CONFORMANCE_SUITE_*.md`; generated input: `CIS_CONFORMANCE_SUITE_INPUT.spec.json`; generation tests under `tests/release/` | **partial** — suite generation/spec **declared**/frozen companion; full executable validation still tied to CORI proof |
| 5 | Validate conformance through implementation | Learn from software, not from further architectural expansion | CORI Alpha Minimal Runtime Proof Plan + dashboard status (“In Progress” slices) | **roadmap** → **partial** as slices close — do not claim **enforced** until green proof package |

---

## Declared vs built (summary)

| Surface | Declared | Built / tested |
|---------|----------|----------------|
| CEOS v1.0 freeze | Yes (**declared**) | No software gate |
| CIS Core normative baseline | Yes (frozen docs) | N/A (spec layer) |
| Reference Architecture | Specs / mapping present | Not a single “CEOS RA” product binary |
| ADR framework | Yes (`docs/adr/`) | Used; disposition rule **declared** |
| Constitutional Kernel (SOCK) | Spec + schema + packages family | Spec **declared**; runtime packages **partial** — not “kernel complete” |
| CORI Alpha | Proof chain + milestone note | Runtime artifacts + tests **partial**; milestone **not** proven |
| Executable conformance | Suite specs + generators | **partial**; not full CEOS conformance product |

---

## Recommended next implementation slice (“demonstrate in software”)

Ship the smallest CORI Alpha vertical that already matches the frozen proof chain — **one replayable path**:

1. **Identity** record tied to a CIS requirement  
2. **Evidence** package written to ledger  
3. **Constitutional State Record**  
4. **Constitutional Receipt** (verifiable)  
5. **Replay** without hidden state  
6. **Conformance** check against generated suite input  

Anchor docs:

- [`../crk1/release/CORI_ALPHA_MILESTONE_NOTE.md`](../crk1/release/CORI_ALPHA_MILESTONE_NOTE.md)
- [`../crk1/release/CORI_ALPHA_PROOF_CHAIN.md`](../crk1/release/CORI_ALPHA_PROOF_CHAIN.md)
- [`../crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_PROOF_PLAN.md`](../crk1/release/CORI_ALPHA_MINIMAL_RUNTIME_PROOF_PLAN.md)

Verification command (existing; re-run for fresh evidence):

```bash
# from G:\project-infi — adjust filter if workspace scripts differ
corepack pnpm exec vitest run tests/release/cori-alpha-proof.test.ts
```

Success for this slice = objective evidence package under `.runtime/cori-alpha/` (or successor path) plus green proof test — **not** new architecture documents.

---

## Evidence-driven architecture rule

Architectural discussion after this point must be **evidence-driven**. Implementation findings are classified per [`ADR_DISPOSITION.md`](./ADR_DISPOSITION.md):

1. ADR  
2. Future profile  
3. Reference architecture clarification  
4. Future specification revision (**only if necessary** — normative gap)

---

## Out of scope for near-term

- New constitutional layers or product names outside Infinity / AAES-OS crown  
- Merging AIKI or Sovereign X CCS into CEOS  
- Hardware / photonic / quantum enforcement claims  
- Upgrading maturity tags without tests
