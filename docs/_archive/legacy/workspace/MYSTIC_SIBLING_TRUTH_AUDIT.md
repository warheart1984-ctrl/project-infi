# Mystic Sibling Truth Audit

Snapshot date: 2026-04-16

Scope:

- `C:\Users\randj\Desktop\project infi\mystic`

Goal:

- identify the real current entry path
- add the missing root truth anchor
- classify keep/archive/quarantine decisions before deeper cleanup

## Current Truth

The `mystic` sibling is a flat root-level prototype.

Supported current entry flow:

1. [`mystic/README.md`](</C:/Users/randj/Desktop/project infi/mystic/README.md>)
2. [`mystic/package.json`](</C:/Users/randj/Desktop/project infi/mystic/package.json>)
3. [`mystic/page.tsx`](</C:/Users/randj/Desktop/project infi/mystic/page.tsx>)
4. [`mystic/route.ts`](</C:/Users/randj/Desktop/project infi/mystic/route.ts>)
5. [`mystic/types.ts`](</C:/Users/randj/Desktop/project infi/mystic/types.ts>)
6. [`mystic/mythic-engine.ts`](</C:/Users/randj/Desktop/project infi/mystic/mythic-engine.ts>)

Operational evidence:

- `package.json` declares a `next` app with `dev`, `build`, and `start`
  scripts
- `layout.tsx`, `page.tsx`, `route.ts`, `globals.css`, and root component files
  define the current prototype surface
- there are no authored subdirectories beyond `.git`

## Missing Entry Docs Identified

Missing before this pass and now added:

- `mystic/README.md`

No deeper folder entry docs are needed right now because the project is flat at
the root.

## Keep / Archive / Quarantine

### Keep As Current

- `package.json`
- `next.config.ts`
- `tailwind.config.ts`
- `postcss.config.js`
- `tsconfig.json`
- `globals.css`
- `layout.tsx`
- `page.tsx`
- `route.ts`
- `types.ts`
- `mythic-engine.ts`
- root component files such as `daily-protocol.tsx`, `journal-form.tsx`,
  `metrics-grid.tsx`, `reading-card.tsx`, and `timeline-card.tsx`

### Keep As Reference Or Archive

- `Mythic-ai-nextjs-v1.docx`
- `mythic-ai-production.zip`
- `mythic-ai.zip`
- `mythic_ai_dashboard_v_1.jsx`

### Quarantine Candidate

- `export type MythicState =.py`

Reason:

- it duplicates logic and types already represented in the active TypeScript
  files
- it has a malformed filename and should not be treated as part of the clean
  current entry path

## Structural Drift To Fix Later

The current prototype has import-path drift:

- files import from `@/components/*` and `@/lib/*`
- but the project is still flat at the root and has no real `components/` or
  `lib/` folders

That is a later structural cleanup item, not an entry-doc problem.

## Result Of This Pass

- `mystic` now has a real root truth anchor
- the current implementation lane is defined without treating the `.docx` or
  `.zip` files as equal authority
- the malformed duplicate Python lane is flagged for quarantine before deeper
  structural work
