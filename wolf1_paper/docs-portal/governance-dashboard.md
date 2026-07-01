# Governance Dashboard

The Governance Dashboard is the primary observability surface for AAES-OS constitutional operations. It provides a transparent, verifiable, and immutable view of governance activity across the system.

## Purpose

The dashboard exists to ensure:

- **Governance transparency**
- **Evidence-based accountability**
- **Traceability of architectural decisions**
- **Continuity of institutional memory**

It is the public-facing window into the AAES-OS governance lifecycle.

## Data sources

### 1. Governance receipts

Each document build produces a cryptographically signed receipt containing version, commit hash, SHA-256 checksums, timestamps, CTS status, and builder identity.

### 2. Requirements registry

Defines constitutional requirements governing runtime behavior, architectural decisions, evidence standards, and amendment processes.

### 3. CTS results

The Constitutional Test Suite validates registry integrity, ADR completeness, requirement traceability, amendment ordering, and specification references.

### 4. Governance events

An append-only feed of receipts, amendments, and build activity (`governance/events.json`).

## Hosting

The dashboard is fully static — no backend required. Deploy `governance/` and `registries/` to any static host.

**Entry point:** `governance/dashboard.html`
