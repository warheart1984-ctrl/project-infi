# Forensic Triangulation Ledger

CISIV stage: **implementation** (MVP live — see [../../subsystems/forensics/TRIANGULATION.md](../../subsystems/forensics/TRIANGULATION.md))

Status: partial live — CLI correlator. Proof: [../../proof/forensics/TRIANGULATION_V1_PROOF.md](../../proof/forensics/TRIANGULATION_V1_PROOF.md)

## 1. Purpose

Correlate diagnostic claims from **AI Mechanic** (workflow/repo forensics),
**Scorpion** (OS trace forensics), and optional **AI Slingshot** (kinetic frame)
into one governed ledger per `case_id`.

Operators today must manually cross-reference artifact trees under
`.runtime/mechanic/`, `.runtime/scorpion/`, and `.runtime/slingshot/`. This
concept unifies them without inventing a fourth forensics engine.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Triangulation does not bypass Mechanic, Scorpion, or Slingshot authority. It
**reads** their ledgers and emits correlation edges only.

## 3. Non-Goals

- No auto-apply or repo mutation (MA-13, MECH-APPLY-01)
- No free-form Jarvis chat wiring (MECH-CHAT-01) — structured tool envelope only
- No kernel Sentinel requirement (Scorpion Stage 4) — fixture traces suffice for v1
- No replacement for subsystem-native ledgers

## 4. Artifact Contract

Schema: [schemas/triangulation.v1.json](./schemas/triangulation.v1.json)

| Field | Role |
|-------|------|
| `triangulation_version` | Must be `triangulation.v1` |
| `case_id` | Shared key across runtime roots |
| `sources` | Hashes/paths for Mechanic, Scorpion, Slingshot inputs |
| `claims` | Normalized Trust Bundle records per source |
| `correlation_edges` | Paired claims with correlation rationale |
| `cisiv_stage` | Staged summary for the correlator output |
| `claim_label` | Overall pack posture: `asserted` / `proven` / `rejected` |

Runtime layout (proposed):

```text
.runtime/triangulation/<case_id>/
  triangulation.v1.json
  correlation_ledger.jsonl
```

## 5. Correlation Model

Each **correlation edge** links two claims:

- `source_a` / `claim_id_a` — e.g. Mechanic `GOV-CI-03`
- `source_b` / `claim_id_b` — e.g. Scorpion drift on `execve` spike
- `correlation_type` — `temporal`, `causal_hypothesis`, `invariant_overlap`
- `rationale` — 1–5 lines (Trust Bundle `why_short` style)
- `claim_label` — edge-level posture

Example: Mechanic reports missing CI gate; Scorpion shows deploy-window syscall
spike — edge typed `temporal` with `asserted` until cross-fixture replay proves
the link.

## 6. Jarvis Handoff (Future)

Structured tool envelope (not chat):

```json
{
  "tool": "forensic_triangulation",
  "case_id": "customer-acme-001",
  "include_slingshot": true
}
```

Response cites `triangulation.v1.json` summary and top correlation edges only.

## 7. Failsafe

- Missing any required source → emit partial correlator with `claim_label: asserted`
- Conflicting claim labels across sources → surface both; do not auto-resolve
- Slingshot `launch_blocked: true` → triangulation MUST NOT downgrade block reason

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema validates fixture correlator output | `asserted` | Schema + manual review only |
| One proven cross-subsystem correlation edge | `none_yet` | Requires implementation + fixture replay |
| Jarvis tool route admitted | `none_yet` | Requires structure stage |

Target proof packet: `docs/proof/forensics/TRIANGULATION_V1_PROOF.md` (not yet
created).

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema |
| Identity | Shared `case_id` contract across runtime roots |
| Structure | `forensics/triangulation.py` or `src/triangulation/` + pytest fixtures |
| Implementation | CLI `python -m triangulation correlate --case-id demo` |
| Verification | Cross-fixture proof with at least one `proven` correlation edge |

## 10. Related

- [../../subsystems/mechanic/MECHANIC_BLUEPRINT.md](../../subsystems/mechanic/MECHANIC_BLUEPRINT.md)
- [../../subsystems/scorpion/SCORPION_BLUEPRINT.md](../../subsystems/scorpion/SCORPION_BLUEPRINT.md)
- [../../runtime/AI_SLINGSHOT.md](../../runtime/AI_SLINGSHOT.md)
- [../../TRUST_BUNDLE_SPEC.md](../../TRUST_BUNDLE_SPEC.md)

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** 2 of 3 — after Lineage Console

**Depends on:** AI Mechanic ledger (`.runtime/mechanic/`), Scorpion trace forensics (`.runtime/scorpion/`), optional Slingshot frame (`.runtime/slingshot/`)

**Minimal invariants:**

- Triangulation reads subsystem-native ledgers; it does not bypass Mechanic, Scorpion, or Slingshot authority
- No auto-apply or repo mutation (MA-13, MECH-APPLY-01)
- Slingshot `launch_blocked: true` → triangulation MUST NOT downgrade block reason
- Missing required source → partial correlator with `claim_label: asserted`
- Conflicting claim labels across sources → surface both; do not auto-resolve
