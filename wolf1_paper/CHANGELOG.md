# CHANGELOG — WOLF-1 Architecture

## 1.2.0 — Governance Dashboard & Receipt Ledger

### New features

- **Governance Dashboard** (`governance/dashboard.html`) — CTS status, documents built, open ADRs, receipts, requirements, event feed
- **Receipt index pipeline** — `governance/receipts-index.json` aggregated on each build
- **Dashboard loader** — client-side loader with dark/light theme toggle
- **Traceability graph** — `governance/graph.html` (Mermaid: requirements → ADRs → artifacts)
- **Governance event feed** — `governance/events.json` from receipts and amendments
- **Makefile integration** — `make all` refreshes dashboard artifacts

### Governance impact

Establishes AAES-OS as a self-auditing constitutional system with transparent governance, immutable evidence trails, and traceable architectural decisions.

## 1.1.0 — 2026-06-25

- Added invariant promotion criteria (Section 4.9).
- Added meta-governance of CRK-1 (Section 4.10).
- Added epistemic receipts (Section 6.4).
- Added graded safe-mode profiles S0–S3 (Section 8.5).
- Added anomaly discovery framework (Section 12.4).
- Added constitutional evolution protocol (Section 14).
- Architectural review by Bradley Bates (SkillsMcGee); see `docs/wolf1/Bradley_Bates_Critique_Resolution_Map.md`.
