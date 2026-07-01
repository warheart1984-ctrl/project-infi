# wolf1_paper

Canonical source and **governed document pipeline** for **WOLF-1: Copilot in Orbit — Architecture Document v1.1**.

## Quick start

```bash
cd wolf1_paper
npm install
npm run build:all    # CTS → PDF/HTML → changelog → amendments → receipt → ADR index → diagrams
```

Or with Make (Git Bash / Linux / macOS):

```bash
make install
make pdf           # CTS gate + versioned PDF/HTML
make all           # full pipeline (no Zenodo/GitHub publish unless tagged)
```

## Version manifest

All builds read `.governance/version.yaml`:

```yaml
documents:
  - id: wolf1-arch
    current_version: 1.1.0
    source: src/wolf1_v1.1.md
    outputs:
      - build/wolf1_v1.1-1.1.0.pdf
      - build/wolf1_v1.1.pdf   # alias (latest build)
```

Bump `current_version` when releasing; outputs are named `wolf1_v1.1-<version>.pdf`.

## Layout

```
.governance/version.yaml   # document IDs, versions, outputs
src/wolf1_v1.1.md          # canonical master
src/sections/              # modular sections (sync from master)
src/sync_sections_from_master.js
build/                     # versioned PDF + HTML artifacts
cts/run_all.mjs            # governance validation gate (runs before PDF)
scripts/                   # changelog, amendments, receipt, publish stubs
governance/receipts/       # DOC-REC-*.json per build
adr/                       # architecture decision records
amendments/                # amendment markdown
CHANGELOG.md
metadata/zenodo.json
assets/diagrams/           # Mermaid (also generated from specs/)
specs/diagram-specs.yaml
```

## Governance dashboard

Static dashboard (no backend): `governance/dashboard.html`

```bash
# After make receipt (or make all)
npx serve .   # open /governance/dashboard.html
```

Loads:
- `governance/receipts-index.json` — aggregated from `governance/receipts/*.json` on each build
- `registries/requirements.yaml` — requirements traceability

## Make targets

| Target | Action |
|--------|--------|
| `make cts` | Validate manifest, registries, ADRs, amendments, specs |
| `make pdf` | CTS + build `build/wolf1_v1.1-<version>.pdf` and `.html` |
| `make receipt` | Emit signed JSON receipt + refresh `receipts-index.json` |
| `make receipt-index` | Regenerate `governance/receipts-index.json` only |
| `make dashboard` | Ensure receipt index is current for static dashboard |
| `make changelog` | Append ADR bullets to CHANGELOG |
| `make amendments` | Generate diff markdown in `build/` |
| `make receipt` | Emit `governance/receipts/DOC-REC-*.json` |
| `make adr-index` | Regenerate `adr/INDEX.md` |
| `make diagrams` | Regenerate flowchart `.mmd` from `specs/` |
| `make zenodo` | Publish stub (requires `ZENODO_TOKEN`) |
| `make github` | `gh release create` on tag |
| `make docs` | Stage artifacts for docs portal |

## PDF engine

- **pandoc** (preferred) when installed
- **puppeteer** fallback via `npm run build:pdf` on Windows without LaTeX

## Collaborator credit

**Bradley Bates** (SkillsMcGee) — architectural review; Sections 4.9, 4.10, 6.4, 8.5, 12.4, 14.

See `docs/wolf1/Bradley_Bates_Critique_Resolution_Map.md` in the parent repo.

## CI

`.github/workflows/wolf1-governed-docs.yml` runs on tags `wolf1-v*` and uploads versioned artifacts + governance receipts.
