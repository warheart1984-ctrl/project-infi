# Contributing to AAES-OS

AAES-OS is a governed system. Contributions must respect the constitutional architecture and invariant model.

## Core principles

1. **No conceptual drift** — do not add invariants, governance surfaces, or object types without explicit approval.
2. **Determinism first** — preserve deterministic execution.
3. **Receipts, or it didn't happen** — new behavior must produce receipts or integrate with the ledger.
4. **Governance is not optional** — features must pass through the InvariantEngine.
5. **Governance evaluates; evidence adopts** — governance determines how changes are evaluated; evidence determines whether changes are adopted. See [`constitution/Governance-Charter.md`](constitution/Governance-Charter.md#evaluation-vs-adoption).

## Workflow

### 1. Open an issue

Describe what you want to change, why, which invariants it touches, and whether it affects determinism.

### 2. Governance review

The Governance Council reviews proposals for constitutional compliance, deterministic safety, invariant impact, and ledger implications.

### 3. Submit a PR

Requirements:

- Tests included
- CTS passes (`pnpm test`, `pytest tests/crk1`)
- No hidden state
- No nondeterministic branches

### 4. Receipt verification

PRs must produce valid spans, valid receipts, and no governance violations.

## Adding invariants

**Forbidden** in v1.0 unless evidence-driven and approved by the Governance Council post-replication.

## Adding runtime features

Must include span emission, ledger integration, governance validation, and deterministic replay tests.

## Coding standards

- TypeScript strict mode in `aaes-os/`
- pnpm workspace conventions
- No side-effects outside runtime lifecycle

## Documentation

Governance changes require updates under [`constitution/`](constitution/) and [`registries/`](registries/).

Thank you for strengthening the constitutional spine of AAES-OS.
