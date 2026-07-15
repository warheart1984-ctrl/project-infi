# AAES-OS v1.x First Implementation Slice

Status: Documentation-first, sprint 1

## What this slice is

This slice converts the extraction plan into the first concrete, repository-filed AAES-OS implementation wedge.
It is intentionally narrow: repository filing, spec navigation, governance traceability, and an example application path.
It does not claim new runtime behavior, service implementations, or enterprise, federation, or research capabilities.

## In scope

- Repository filing for the five extracted spec docs and their docs-site mirrors
- API reference stabilization by keeping versioned surface language explicit and avoiding invented APIs
- Governance traceability across the handbook, engineering spec, standards, governance spec, and roadmap
- Example application path for contributors: start with this slice, then follow the spec set in reading order

## Out of scope

- New runtime services or agent behavior
- Enterprise, federation, research, or lab expansion
- New plugin registries, new release systems, or new claims about operational readiness

## Traceability matrix

| Extracted spec doc | Repository filing | docs-site page | What this slice makes concrete | Next implementation work |
| --- | --- | --- | --- | --- |
| AAES-OS Engineering Handbook | `docs/specifications/aaes-os-engineering-handbook.md` | `docs-site/docs/specifications/aaes-os-engineering-handbook.md` | Contributor-facing principles, runtime shape, repository standard, and release posture | Use as the first read before any code or doc changes |
| AAES-OS Engineering Specification | `docs/specifications/aaes-os-engineering-specification.md` | `docs-site/docs/specifications/aaes-os-engineering-specification.md` | Versioned API rules, module boundaries, and testing expectations | Keep API surfaces versioned and traceable before implementation expands |
| AAES-OS Engineering Standards | `docs/specifications/aaes-os-engineering-standards.md` | `docs-site/docs/specifications/aaes-os-engineering-standards.md` | Repository requirements, coding standards, API standards, and release hygiene | Use as the baseline for repository filing and change review |
| AAES-OS Governance Specification | `docs/specifications/aaes-os-governance-specification.md` | `docs-site/docs/specifications/aaes-os-governance-specification.md` | Evidence model, audit model, approval workflow, and constitutional invariants | Apply the governance vocabulary before adding runtime claims |
| AAES-OS Product Roadmap | `docs/specifications/aaes-os-product-roadmap.md` | `docs-site/docs/specifications/aaes-os-product-roadmap.md` | Release sequencing and explicit future milestones | Keep v1.x work bounded to the stable core, not later roadmap items |

## Example application path

1. Open this slice and confirm the scope is documentation-first.
2. Read the engineering handbook for the contributor baseline.
3. Read the engineering specification and standards together to keep API and repository expectations stable.
4. Read the governance specification to keep evidence and audit language consistent.
5. Read the product roadmap to separate the v1.x slice from later enterprise, federation, and research work.
6. Use the traceability matrix to decide the next implementation task instead of expanding scope inside this slice.

## Slice checklist

- [x] Canonical docs filed in `docs/specifications`
- [x] Docs-site mirror filed in `docs-site/docs/specifications`
- [x] Specification navigation exposes the slice
- [x] Docs hub links the slice for discoverability
- [x] Smoke verification checks the built slice page

## What comes next

The next implementation work should turn this documentation slice into concrete repository tasks without broadening scope:

- Keep repository filing synchronized between the source docs and docs-site mirror
- Keep public API references versioned and explicit
- Keep governance traceability attached to any new runtime or service claims
- Keep the example application path aligned to the first sprint-worthy chunk only
