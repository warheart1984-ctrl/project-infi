# Top-Level Workspace Root Relocation Plan

Snapshot date: 2026-04-16

Scope:

- `C:\Users\randj\Desktop\project infi`
- one layer above `AAIS-main`

Execution status:

- planned: 2026-04-16
- executed: 2026-04-16
- current outcome: the loose root file layer now contains only
  `WORKSPACE_INDEX.md` and `.gitattributes`
- sensitive note status: `Arisevlvenapikey.txt` was removed from the root file
  layer and quarantined into a hidden `.local-secrets/` folder that is excluded
  from the parent repo's local Git exclude file

Goal:

- reduce root-level document drift
- keep the workspace root understandable at a glance
- prevent loose doctrine/spec files from being mistaken for current canonical
  truth
- move archive/reference material into explicit archive buckets before any
  project-specific curation happens

## Root Rule

The workspace root should keep only:

- project folders
- minimal workspace metadata
- one workspace entry document

For the current root, keep in place:

- [`WORKSPACE_INDEX.md`](../../../WORKSPACE_INDEX.md)
- `project folders`
- `.gitattributes`

Everything else at the root file layer should either be archived, relocated to
an owning project, or quarantined if sensitive.

## Current Root File Counts

- `45` `.docx` files
- `3` `.md` files
- `3` `.txt` files
- `3` `.zip` files

## Immediate Security Action

Do not archive this file into shared workspace history:

- `Arisevlvenapikey.txt`

Required action:

- remove it from the workspace root immediately
- move the secret into a private local secret store or per-project `.env`
  handling outside the root loose-file layer
- if obsolete, delete it instead of preserving it as a casual note

## Proposed Archive / Relocation Buckets

Create or use these workspace-root archive buckets:

- `_archives/workspace-root-docs/cuos-law/`
- `_archives/workspace-root-docs/project-infi-runtime/`
- `_archives/workspace-root-docs/jarvis-and-behavioral/`
- `_archives/workspace-root-docs/nova-aris-ui/`
- `_archives/workspace-root-docs/evolve-engine-and-implementation/`
- `_archives/workspace-root-docs/misc-reference/`
- `_archives/workspace-root-docs/legacy-md/`
- `_archives/workspace-root-notes/`
- `_archives/release-bundles/`
- `_archives/zip-backups/root-copies/`

## Exact Move Map

### Keep At Root

- `WORKSPACE_INDEX.md`
- `.gitattributes`

### Quarantine Instead Of Archiving

- `Arisevlvenapikey.txt`

### Move To `_archives/workspace-root-docs/legacy-md/`

- `Jarvis_Trust_Standard.md`
- `Lawful Completion of a System.md`

Notes:

- `Lawful Completion of a System.md` already has a clearer operational home in
  [`code/code/LAWFUL_COMPLETION_OF_A_SYSTEM.md`](</C:/Users/randj/Desktop/project infi/code/code/LAWFUL_COMPLETION_OF_A_SYSTEM.md>).
- keep the root free of parallel markdown authority copies

### Move To `_archives/workspace-root-notes/`

- `Repository documentation exists not.txt`
- `The Vision.txt`

### Move To `_archives/zip-backups/root-copies/`

- `AAIS-main.zip`
- `code.zip`

Important note:

- these are not byte-identical to the archived copies already under
  `_archives/zip-backups/`
- keep them as distinct archived artifacts with dated or suffixed filenames
  rather than overwriting the older backups

### Move To `_archives/release-bundles/`

- `ARIS Demo Desktop.zip`

### Move To `_archives/workspace-root-docs/cuos-law/`

- `# Cognitive Unified OS — Developer Handbook adds.docx`
- `# Cognitive Unified OS Ecosystem.docx`
- `⭐ Cognitive Unified OS — Origin Integrity Law (Final, Canonical).docx`
- `📘 Document_ Laws of AI Governance (CISLR _ UL Runtime).docx`
- `Cislr Runtime blueprint.docx`
- `Cognitive Unified OS — Law Enforcement Map.docx`
- `Cognitive Unified OS — Platform Law.docx`
- `Cognitive Unified OS 0 — Platform Law.docx`
- `Combined Foundation Law.docx`
- `Foundation Law Enforcement Points .docx`
- `UL Doctrine — Law of First Mutanage (1001).docx`

### Move To `_archives/workspace-root-docs/project-infi-runtime/`

- `Binary Operators (produce each state inside one cycle).docx`
- `debt accounty layer.docx`
- `Project Infi _ ARIS Runtime Chronos Gate.docx`
- `Project Infi _ ARIS Runtime Master Spec 1.1.docx`
- `Project Infi _ ARIS Runtime time model.docx`
- `Project Infi _ ARIS Runtime.docx`
- `Project Infi — Legitimacy Gate (Pre-Mutation Law).docx`
- `Project Infi — The Voss Binding (Λ) Formal Specification.docx`
- `Project Infi — UL Governance & State Transition Model (2).docx`
- `Project Infi — UL Governance & State Transition Model.docx`
- `project Infi — UL Governed Runtime (Master Specification v1.docx`
- `Project Infi — UL Governed Runtime Model (Complete).docx`
- `trace model.docx`

### Move To `_archives/workspace-root-docs/jarvis-and-behavioral/`

- `JARVIS BEHAVIORAL CORE v1.docx`
- `Jarvis Turn Engine.docx`
- `Jarvis_Trust_Standard.docx`
- `Repo A.i LIke Codex.docx`
- `ROUTING DOCUMENT.docx`
- `Hall of SHame ( never leaves the Hall).docx`
- `v1.3 consolidated Behavioral Core (all sections merged cleanly).docx`
- `v1.3.1 consolidated Behavioral Core (all sections merged cleanly).docx`

### Move To `_archives/workspace-root-docs/nova-aris-ui/`

- `📘 ARIS User Manual (v1).docx`
- `aris Layout — CSS Grid Shell.docx`
- `Codex Controls V1 — Markdown Spec.docx`
- `light bulb, wards and shields _ layered with emontional , reasoning , idenity, but baked into nova.docx`
- `nova local server and ui .docx`

### Move To `_archives/workspace-root-docs/evolve-engine-and-implementation/`

- `baseline.docx`
- `evlove engine handbook.docx`
- `install the evolve engine.docx`
- `The implementation order.docx`
- `🧩 Why this is the correct integration pattern.docx`

### Move To `_archives/workspace-root-docs/misc-reference/`

- `Lawful Completion of a System.docx`
- `NOTICE.docx`
- `The key rule for all 6_.docx`

## Unresolved Ownership Ambiguities

These files should still leave the workspace root now, but their eventual
long-term owner is not fully settled:

- `Codex Controls V1 — Markdown Spec.docx`
  - could later map to `Ui jarvis` or a future AAIS UI archive lane
- `evlove engine handbook.docx`
  - could later map to `code/code` or `AAIS-main/evolve_engine`
- `install the evolve engine.docx`
  - same ambiguity as the handbook
- `Repo A.i LIke Codex.docx`
  - could later map to Jarvis lineage or Project Infi runtime lineage
- `nova local server and ui .docx`
  - could later map to `Nova, The North Star` or the AAIS Nova subsystem
- `light bulb, wards and shields _ layered with emontional , reasoning , idenity, but baked into nova.docx`
  - likely Nova lineage, but not current canonical runtime truth
- `🧩 Why this is the correct integration pattern.docx`
  - broad integration lineage, not a settled active-owner document

Recommendation:

- archive first into the root-doc buckets above
- only promote into a project-owned docs tree after an explicit ownership
  decision

## Completion Condition

The top-level workspace root is considered cleaned when:

- only `WORKSPACE_INDEX.md`, `.gitattributes`, and project folders remain at the
  loose root file layer
- the secret text file is no longer loose at root
- all root `.docx`, legacy `.md`, `.txt`, and `.zip` artifacts are either
  archived or intentionally relocated
- archived files are labeled as reference/archive rather than active truth

Current status:

- complete for the root loose-file layer covered by this plan
