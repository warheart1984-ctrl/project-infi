# AI Mechanic Blueprint

## Canonical Definition

AI Mechanic is a governed **enterprise AI workflow forensics** subsystem: it scans arbitrary code repositories, builds a **Process Genome**, diagnoses structural failures against a constitutional invariant catalog (GOV/RNT/CST/HUM), and emits **dry-run rebuild** artifacts.

It is not a consultant slide deck, not a model zoo, and not an auto-patcher.

## Purpose

Convert real AI workflow topology (prompts, agents, automations, CI, Python LLM calls) into bounded diagnostic claims and reconstruction plans—without mutating customer repos in MVP.

## Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

AI Mechanic cannot bypass repository law or MA-13 (Stage 2 Copilot Doctrine).

## Five Components

| Component | Responsibility |
|-----------|----------------|
| **Genome Extractor** | Crawl repo via adapters → `process_genome.v1` |
| **Diagnosis Engine** | Catalog + evaluators → `mechanic_scan.v1` |
| **Ledger** | Diagnostic claims (`asserted`, `proven`, `rejected`) |
| **Rebuild Planner** | Target workflow, patch plan, runtime profile (dry-run) |
| **Historian** | Append-only health drift index |

## Non-Goals (MVP)

- LLM-based process reconstruction (MECH-LLM-01)
- Interview / tribal knowledge ingest (MECH-TRIBAL-01)
- Auto-apply or `apply` mode (MECH-APPLY-01)
- Jarvis chat wiring (MECH-CHAT-01)

## Failsafe

- Default: observe / scan / diagnose / rebuild (artifacts only)
- `apply` mode **blocked** at CLI
- Rebuild proposals marked `provisional` where they add structure

## Related

- [MECHANIC_CLI_CONTRACT.md](./MECHANIC_CLI_CONTRACT.md)
- [INVARIANT_CATALOG.md](./INVARIANT_CATALOG.md)
- [STAGE2_COPILOT_DOCTRINE.md](../../runtime/STAGE2_COPILOT_DOCTRINE.md)
