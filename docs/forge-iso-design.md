# Forge ISO Self-Hosting Architecture Design

Status: canonical location under `docs/` (migrated from `document/programs/forge-iso-design.md`).

This file is the long-term canonical path per repo-law. Design/blueprint changes for Forge ISO architecture should be maintained here.

## Migration note

- Previous path: `document/programs/forge-iso-design.md`
- Canonical path: `docs/forge-iso-design.md`
- Migration approach: safe normalization by introducing canonical `docs/` artifact without deleting legacy planning copy in this pass.

## OS-agnostic replay substrate

Forge accepts **any compatible hybrid live ISO** as replay input (squashfs under `live/` + boot replay via xorriso). Rootfs construction may still use Debian/debootstrap; that is separate from substrate selection.

See `docs/forge-substrate-contract.md` and `wolf-cog-os/forge/substrates/registry.json`.
