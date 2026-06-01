# SEAM-VC-002

## Title

Visible Scaffold Leakage Across Operator Surfaces

## Classification

- seam class: `output_shape_seam`
- secondary class: `governance_seam`
- boundary type: internal or machine output to operator-facing surface
- severity: high
- status: closed for covered surfaces in this repository
- discovery state: verified by regression and multi-surface audit

## Summary

Internal scaffold artifacts such as `Mode:`, `Focus:`, and `Answer Shape:`
were leaking into operator-visible outputs across more than one surface.

The seam was distributed across:

- chat visible reply finalization
- Forge contractor summaries
- ForgeEval summaries
- evolve to Forge handoff summaries
- frontend summary field selection

## First Signal

Operator-facing replies and summaries contained machine-oriented scaffold
headers instead of only the real answer or bounded summary.

## Why It Stood Out

The failure reproduced across distinct surfaces, which meant the issue was not
just one bad reply path. The same internal shape bleed appeared in chat and in
Forge-facing summaries, indicating a shared boundary problem around visible
operator output.

## Seam Class

- primary: `output_shape_seam`
- secondary: `governance_seam`

## Boundary

`internal/machine output -> operator-visible surface`

Covered runtime boundaries in this repo:

- answer generation -> visible reply finalization
- Forge contractor result -> operator-safe summary
- ForgeEval result -> operator-safe summary
- evolve handoff analysis -> operator-safe summary
- frontend summary field selection -> rendered operator text

## Symptoms

- visible replies showing scaffold labels such as:
  - `Mode: think`
  - `Focus: ...`
  - `Answer Shape: ...`
- operator summaries containing flattened internal scaffold blocks
- mixed content being over-corrected when cleanup misclassified the whole blob
  as pure scaffold

## Root Cause

### Primary Cause

Scaffold cleanup was not enforced consistently at every operator-visible
boundary.

### Secondary Causes

#### Surface Fragmentation

Cleanup existed in the chat finalization path, but equivalent operator-safe
cleanup was missing from Forge and related summary paths.

#### Pre-Cleanup Mutation

One evolve-to-Forge handoff path flattened the summary before cleanup, which
damaged structure and made the cleanup logic more likely to classify the full
payload as scaffold.

#### Frontend Field Preference

The operator console could render `analysis.summary` instead of a sanitized
operator-safe field.

## Law

No internal scaffold artifacts may reach covered operator-visible surfaces.

At these boundaries:

- raw machine truth may be preserved for audit and evaluation
- operator-facing text must be scaffold-clean
- cleanup must happen at the final visible boundary, not by mutating raw truth
  upstream

## Resolution

### 1. Unified Visible-Surface Cleanup

Applied scaffold stripping across the covered operator-visible boundaries:

- shared chat finalization
- operator-surface cleanup helper
- Forge contractor summary sanitization
- ForgeEval summary sanitization
- evolve to Forge handoff summary sanitization

### 2. Pre-Cleanup Integrity Fix

Removed premature summary flattening before cleanup on the evolve-to-Forge
handoff path so cleanup could evaluate structured multiline content.

### 3. Dual-Channel Output Separation

Preserved two channels:

- raw payload
  full-fidelity machine output retained for audit and evaluation
- operator-safe summary
  scaffold-clean text for display

### 4. Frontend Alignment

Updated the operator console to prefer `operator_safe_analysis_summary` over
`analysis.summary`.

## Enforcement

Backend enforcement landed in:

- `src/api.py`
  - shared visible scaffold cleanup for chat replies
  - operator-surface text sanitizer with domain-safe fallback behavior
  - Forge, ForgeEval, and evolve handoff summary cleanup

Frontend enforcement landed in:

- `frontend/src/pages/JarvisConsole.jsx`
  - preferred sanitized summary field for rendering

## Verification

Regression coverage proves:

- scaffold stripping in Forge summaries
- scaffold stripping in evolve handoff summaries
- mixed-content preservation where the real answer survives and scaffold headers
  are removed
- frontend build remains valid after the rendering-field change

Verification commands:

```bash
python -m pytest tests/test_api.py -k "forge or evolve or visible_scaffold or output_completion" -q
npm --prefix frontend run build
```

Result:

- targeted Forge, evolve, and visible-scaffold regressions passed
- the broader Forge and output-cleanup sweep passed
- frontend production build passed

## Architectural Impact

### Before

- cleanup applied inconsistently
- operator surfaces could leak internal scaffolding
- some cleanup paths over-corrected because the input had already been degraded

### After

- covered operator-visible surfaces are governed by one scaffold-exposure law
- cleanup is boundary-enforced and structure-aware
- raw machine truth is preserved separately from operator-facing text

## Proof Statement

No known internal scaffold artifacts reach the covered operator-visible
surfaces in this repository across chat, Forge, ForgeEval, or evolve handoff
paths, while raw machine payloads remain intact for audit and evaluation.

## Remaining Gap

### ARIS Surface Not Located

No distinct ARIS runtime, API, or UI surface was found in:

- `src/`
- `frontend/src/`
- `tests/`

This is not evidence of a failed seam fix.

It means the target boundary is not present in this repository.

## Key Lessons

- seams rarely live in one path
- cleanup must be enforced at the final visible boundary
- raw machine truth and operator-safe presentation should remain separate
- frontend rendering choice is part of the seam, not outside it

## Doctrine Alignment

This seam validates boundary-first enforcement and dual-channel output design.

The system does not hide truth. It controls exposure.
