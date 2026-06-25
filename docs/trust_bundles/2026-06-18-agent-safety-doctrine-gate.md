claim_label: proven
why_short: |
  MA-14 turns agent safety doctrine into a validated governance surface.
  The validator rejects missing evidence, missing reversal paths, prohibited agent drift, and authority increases under uncertainty.
  Evidence is local and reproducible with the focused pytest command and validator CLI.
proof_links:
  - tests/test_agent_safety_doctrine.py
  - .github/scripts/validate-agent-safety-doctrine.py
  - governance/agent_change_manifests/2026-06-18-agent-safety-doctrine.v1.json
none_yet: false
override_command: git restore -- META_ARCHITECT_LAWBOOK.md REPO_PROOF_LAW.md HUMAN_AI_CO_COLLABORATION_CHARTER.md README.md Makefile .github/scripts/validate-agent-safety-doctrine.py .github/workflows/agent-safety-doctrine-gate.yml .github/workflows/documentation-baseline-gate.yml tests/test_agent_safety_doctrine.py templates/AGENT_SAFETY_DOCTRINE_MANIFEST_TEMPLATE.json governance/agent_change_manifests/2026-06-18-agent-safety-doctrine.v1.json docs/trust_bundles/2026-06-18-agent-safety-doctrine-gate.md
override_breaks_blueprint: false
debt_ticket_ref: none
created_at_utc: 2026-06-18T09:09:30Z
updated_at_utc: 2026-06-18T09:09:30Z
author: codex
context: agent-safety-doctrine-governance-hardening
