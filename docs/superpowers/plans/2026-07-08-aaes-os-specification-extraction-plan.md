# AAES-OS Specification Extraction Plan

> For agentic workers: use the extracted repo specs below as the canonical source for documentation and follow-on implementation work.

**Goal:** Convert the long-form AAES-OS memory bundle into stable repo docs, a wired docs-site section, and a smaller execution plan that future tasks can actually finish.

## Phase 1: Canonicalize the reference docs

- Create `docs/specifications/README.md`.
- Split the memory bundle into five stable specs:
  - engineering handbook
  - engineering specification
  - engineering standards
  - governance specification
  - product roadmap
- Keep the documents reference-grade and non-hallucinatory: only claim what the text supports.

## Phase 2: Wire the docs site

- Add a docs-site section for `AAES-OS Specifications`.
- Link the homepage and sidebar to the new pages.
- Add smoke coverage so the section cannot silently disappear.

## Phase 3: Define the implementation slice

- Pull the roadmap into an actionable one-sprint slice.
- Prioritize:
  - repository filing
  - API reference stabilization
  - governance traceability
  - example application path
- Keep research and future major-version items out of the current sprint.

## Phase 4: Verify and publish

- Confirm the docs render.
- Confirm the sidebar and homepage links resolve.
- Confirm the plan is small enough for a single implementation cycle.

