# Meta Architect Lawbook (local-only)

`META_ARCHITECT_LAWBOOK.md` at the repository root is **gitignored** and is not published to GitHub (Project-Infinity1, URG-Cloud-Platform, or other remotes).

## After clone or pull

Keep your own copy at:

```
META_ARCHITECT_LAWBOOK.md
```

If you previously had the file tracked in git, it remains on disk when removed from the index; new clones must add the lawbook locally (backup, prior checkout, or your governance source).

## CI

The documentation baseline gate **skips** lawbook validation when the file is absent. Local developers and agents should still treat the lawbook as supreme authority when the file is present.

## References elsewhere

Many docs link to `META_ARCHITECT_LAWBOOK.md` by path; those links resolve when your local file exists at the repo root.
