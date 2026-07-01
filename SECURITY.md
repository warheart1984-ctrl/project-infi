# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `0.2.x` (latest on `main`) | Yes |
| Older commits, forks, or archived trees | No |

## Reporting a Vulnerability

Report security issues responsibly:

- **Non-sensitive:** open a [GitHub Issue](https://github.com/warheart1984-ctrl/Project-Infinity1/issues)
- **Sensitive:** email [warheart1984@gmail.com](mailto:warheart1984@gmail.com)

Include a clear description, reproduction steps, impact, and optional mitigation.

We acknowledge reports on a best-effort basis. Confirmed issues receive a fix or documented mitigation.

## Before Production Deployment

This repository ships development defaults. Operators must harden before any production or internet-facing deployment:

1. **Never use development CoGOS signing keys.** Generate fresh trust keys for Wolf-CoG-OS / CoGOS installs. Do not copy keys from local backup bundles under `wolf-cog-os/payload/opt/cogos/memory/backups/` (gitignored, local-only).
2. **Rotate Platform secrets** in `deploy/pilot/.env` or `deploy/platform/.env`: `PLATFORM_MASTER_API_KEY`, `PLATFORM_EXPORT_PACK_SECRET`, `PLATFORM_EXCHANGE_SECRET`.
3. **Protect provider API keys** (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`). Keep `.env` out of git; use your secret manager in production.
4. **Set `APP_BEARER_TOKEN`** if exposing the workflow shell beyond localhost.
5. **Review compose files** under `mechanic/hosted/deploy/` and `deploy/` — placeholder secrets are for local pilot only.

## Secrets in This Repository

The following must never contain real credentials in tracked files:

- `.env` (gitignored)
- Wolf-CoG-OS operator backup snapshots
- Private training data under `training/data/private_messages*.jsonl`
- GitHub Actions secrets (`MINISIGN_*` for CoGOS release promotion)

If you find a committed secret, report it immediately and rotate the affected credential.

## CoGOS ISO Releases

CoGOS stable ISO promotion uses minisign keys stored in GitHub Actions secrets, not in the repo. See [`docs/releases/README.md`](docs/releases/README.md) for the AAIS vs CoGOS release split.
