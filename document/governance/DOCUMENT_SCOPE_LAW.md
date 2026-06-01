# Document Folder Scope Law

## Law

All blueprint and documentation authority artifacts for the canonical root lane
must live under `document/`.

## Canonical Scope

This law applies to the canonical root repository lane at `E:/project-infi`.

## Explicit Exclusions

The following trees are excluded from this migration law and must not be
rewritten during canonical-root migration passes:

- `Project-Infinity-main/` (mirror)
- `Aris--main/` (mirror)
- `archive/` and `**/archive/` lineage trees
- `docs/_archive/` archival documentation
- vendor drops and vendored source trees (for example `**/vendor/**`)

## Enforcement Requirements

1. New canonical blueprint/doc/law/governance/program docs must be created under
   `document/`.
2. Moving canonical docs into `document/` requires reference rewrites in
   canonical code/docs.
3. Migration passes must run stale-path and broken-reference checks before
   completion.
4. If migration scope is ambiguous, implementation must stop and request user
   decision.
