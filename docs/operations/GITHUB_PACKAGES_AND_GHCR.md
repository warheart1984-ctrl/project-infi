# GitHub Packages and GHCR — distribution policy

## Decision (Infinity 1)

**Tier 1 (local AAIS):** Do **not** use GitHub Packages. Operators clone the repo and run [`scripts/start-infinity1.ps1`](../../scripts/start-infinity1.ps1) or [`scripts/start-infinity1.sh`](../../scripts/start-infinity1.sh). Python installs from [`pyproject.toml`](../../pyproject.toml) into a local `.venv`.

**Registries we skip:**

| Registry | Reason |
|----------|--------|
| Apache Maven | Not a Java project |
| NuGet | Not a .NET project |
| RubyGems | Not a Ruby project |
| npm | Frontend is `"private": true`; UI ships prebuilt in `app/static/` |
| PyPI | Optional future; not GitHub Packages. Monorepo + governance gates favor git clone |

**Containers (GHCR):** Optional for **Tier 2 Infinity Pilot** only. Pre-built images avoid local `docker compose build` time. Images publish on version tags (`v*`) via [`.github/workflows/publish-ghcr.yml`](../../.github/workflows/publish-ghcr.yml).

## Current distribution stack

1. **Git clone + bootstrap** — default for operators ([README](../../README.md))
2. **GitHub Releases** — version tags (e.g. `v1.26.1`)
3. **Zenodo** — civilizational maturity audit ([10.5281/zenodo.20587377](https://doi.org/10.5281/zenodo.20587377))
4. **GHCR (optional)** — `ghcr.io/warheart1984-ctrl/project-infinity1/aais` and `/platform`

## Using GHCR images (Infinity Pilot)

Set the tag to match a GitHub release:

```bash
export AAIS_IMAGE_TAG=v1.26.1
export PLATFORM_IMAGE_TAG=v1.26.1
cd deploy/pilot
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up -d
```

Default compose (build locally) remains unchanged:

```bash
docker compose up --build -d
```

### Authentication

Public repo images are pullable without login. For private forks or org-private packages:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u USERNAME --password-stdin
```

Use a PAT with `read:packages` if `GITHUB_TOKEN` from Actions is not available locally.

## When to revisit

- **PyPI** — if you want `pip install aais` without cloning the monorepo
- **npm** — only if you publish a standalone JS SDK
- **Private GHCR** — org-only pilot with package visibility restricted on GitHub
