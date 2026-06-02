# Release Notes

Project Infinity ships **two independent release tracks**. Do not conflate them.

## Track A: AAIS application (semver)

**Scope:** Python runtime, operator UI, launcher, core tests, and documented operator paths.

| Artifact | Location |
|---|---|
| Version | `pyproject.toml` (`aais` package) |
| History | [CHANGELOG.md](../../CHANGELOG.md) |
| Tag format | `v1.3.1` (latest — Close Loops), `v1.3.0`, `v1.2.0`, `v1.1.0`, `v0.2.0`, or `aais-v0.2.0` |
| GitHub Release | Manual or release-drafter; body = CHANGELOG section for that version |
| v1.3.1 notes | [v1.3.1-close-loops.md](./v1.3.1-close-loops.md) |
| v1.3.0 notes | [v1.3.0-alt7-coherence-fabric.md](./v1.3.0-alt7-coherence-fabric.md) |
| v1.2.0 notes | [v1.2.0-alt6-adaptive-lanes.md](./v1.2.0-alt6-adaptive-lanes.md) |
| v1.1.0 notes | [v1.1.0-infinity-complete.md](./v1.1.0-infinity-complete.md) |

### Publishing an AAIS release (maintainer)

1. Complete [pre-tag checklist](../GITHUB.md#pre-tag-release-checklist) in `docs/GITHUB.md`.
2. Ensure `CHANGELOG.md` has a dated section for the version.
3. Tag: `git tag -a v0.2.0 -m "AAIS v0.2.0 — initial public release"`
4. Push tag and create GitHub Release with:
   - **Summary** — one paragraph for operators
   - **Upgrade** — env or migration notes if any
   - **Verification** — copy checklist from CHANGELOG

### Operator-facing summary template

```markdown
## Summary
AAIS vX.Y.Z — [one sentence on what changed for operators]

## Upgrade
- [env changes, breaking API changes, or "no action required"]

## Verification
- curl health + chat smoke
- python -m tools.ul.smoke
- (optional) make stack-pilot-gate
```

---

## Track B: CoGOS ISO (forge promotion)

**Scope:** Wolf-CoG-OS ISO/rootfs builds, installer validation, minisign promotion.

| Artifact | Location |
|---|---|
| Generator | [`.github/scripts/generate-release-notes.py`](../../.github/scripts/generate-release-notes.py) |
| Workflows | `cogos-rc.yml`, `cogos-release.yml` |
| Tag format | `cogos-v*` (CoGOS-specific) |
| Output | Build metadata, installer validation steps, artifact list |

CoGOS release notes are **CI-generated** at promotion time. They include commit range, build metadata, and installer validation status — not AAIS app semver.

Operators building ISOs locally: see [wolf-cog-os/forge/README.md](../../wolf-cog-os/forge/README.md). Outputs land under `wolf-cog-os/output/` (gitignored).

### Secrets

CoGOS stable promotion requires GitHub Actions secrets:

- `MINISIGN_SECRET_KEY`
- `MINISIGN_PUBLIC_KEY`

These are never stored in the repository. See [SECURITY.md](../../SECURITY.md).

---

## Which track do I follow?

| You are… | Follow |
|---|---|
| Running AAIS locally or Infinity Pilot Docker | Track A — CHANGELOG + First-Time Operator Guide |
| Building or installing a CoGOS ISO | Track B — wolf-cog-os docs + CoGOS GitHub Release |
| Contributing code | Both changelogs matter; your PR gate depends on touched paths |
