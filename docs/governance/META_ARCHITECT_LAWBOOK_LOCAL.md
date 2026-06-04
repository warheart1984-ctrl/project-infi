# Local-only docs (not on GitHub)

These files at the **project-infi repo root** are **gitignored** and are not published to GitHub (Project-Infinity1, URG-Cloud-Platform, or other remotes):

| File | Role |
|------|------|
| `META_ARCHITECT_LAWBOOK.md` | Supreme governance authority |
| `REPO_PROOF_LAW.md` | Proof-of-reality and baseline law (implements the lawbook) |
| `HUMAN_AI_CO_COLLABORATION_CHARTER.md` | Human–AI collaboration constitutional companion |
| `CONTRIBUTORS.md` | Maintainer and contributor credits (local roster) |

## After clone or pull

Keep **one copy of each** at the repo root only:

```
META_ARCHITECT_LAWBOOK.md
REPO_PROOF_LAW.md
HUMAN_AI_CO_COLLABORATION_CHARTER.md
CONTRIBUTORS.md
```

Do not keep duplicates under `Project-Infinity1/` or other nested clones. The nested `Project-Infinity1/` tree is gitignored in the canonical workspace.

If files were previously tracked in git, they may remain on disk after `git rm --cached`; new clones must add them locally (backup, prior checkout, or your governance source).

## CI

The documentation baseline gate **skips** lawbook validation when `META_ARCHITECT_LAWBOOK.md` is absent. Checklist and README validation still run on tracked files.

## References elsewhere

Tracked docs (e.g. `README.md`, `CONTRIBUTING.md`) may link to these paths; links resolve when your local files exist at the repo root.
