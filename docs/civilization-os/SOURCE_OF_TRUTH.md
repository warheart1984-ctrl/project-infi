# Civilization OS — Source of Truth vs Noise

**Status:** Housekeeping charter  
**Canonical tree:** `G:\project-infi`  
**Date:** 2026-07-20

---

## Source of truth

| Role | Path |
|------|------|
| **Civilization OS / Infi workspace** | `G:\project-infi` |
| **Identity + organ map** | `G:\project-infi\docs\civilization-os\` |
| **Maturity claims** | `G:\project-infi\docs\scorecards\project-infi.md` only after fresh verification |

Do not treat clones, zips, or “main” mirrors as current unless they **are** `project-infi` or an explicit tagged release.

---

## Noise / secondary copies (do not steer from these)

| Path | Why it’s noise for “current” |
|------|------------------------------|
| `G:\Project-Infinity-main` | Nested / alternate Infinity tree |
| `G:\infi\` | Document stash (blueprints) — valuable archive, not runtime SoT |
| `G:\AAES-OS-clone` | Clone; may diverge |
| `G:\aaes-os` | Sibling / older surface — check before editing |
| `G:\nova-clone`, `G:\nova-backup-*`, `G:\nova-mission-002` | Nova forks/backups |
| `G:\project-infi\nova-mission-002.v0.1.0.bak` | Explicit backup inside SoT tree |
| `G:\archive\**` | Historical downloads/zips |
| `G:\project-infi\drive-g-*.zip`, `drive-g-*.tar.gz` | Full-drive backups inside repo — storage, not edit target |
| `G:\project-infi\release\bundle\artifacts\docs\**` | Bundled doc copies — prefer live `docs/` |

**Rule:** Edit SoT → optionally refresh release bundles. Never edit the bundle and assume SoT updated.

---

## Treasure (keep, but label)

These are high-value **not** because they are the live OS, but because they hold IP/spec memory:

- `G:\assets\documents\governance\` — organism constitutions, Infinity governance corpora  
- `G:\infi\*.docx` — Infinity master / IP / technical systems  
- `G:\archive\downloads\*Infi*` / `*Infinity*` / `*Voss*`  
- Root schemas on `G:\` (`identity.schema.json`, `mission.schema.json`, `substrate.schema.json`, `genome-manifest.json`) — classify before merging into Infi

Move or copy into `project-infi/docs/` **only** when promoting a doc to active charter; otherwise leave and link.

---

## Recommended hygiene (manual; not auto-deleted)

1. Prefix inactive clones with `_archive_` or move under `G:\archive\trees\` when ready.  
2. Add a one-line `CURRENT.md` in any clone pointing to `G:\project-infi`.  
3. Keep `.bak` and zip backups; stop opening them as workspaces in the IDE.

---

## Related

- `IDENTITY.md`  
- `ORGAN_LEDGER.md`
