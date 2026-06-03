# AAIS Alt-4 Runtime Operator Guide

Status: **active contract**

CISIV stage: **structure**

Parent: [AAIS_SSP_PROTOCOL.md](./AAIS_SSP_PROTOCOL.md)

## Purpose

This guide documents how the four Alt-4 runtime organs work together: when they run,
what commands operators use, and how to diagnose failures. Alt-4 is SSP
governance-of-governance made executable — not a keyboard shortcut.

Implementation: `src/governance_organs/` behind the `Alt4Runtime` facade.

## System map

| Organ | Module | Role |
|-------|--------|------|
| Genome Engine | `genome_engine.py` | Validates DNA on boot, gates, and capability-bridge calls |
| Promotion Engine | `promotion_engine.py` | Full-auto `concept → prototype → mvp → governed` |
| Mutation Engine | `mutation_engine.py` | MP-X apply/rollback with `schemas/deltas/` |
| Retirement Engine | `retirement_engine.py` | 10-step retirement state machine |

| Lifecycle path | Engine |
|----------------|--------|
| Stage advance | Promotion |
| Backward-compatible evolution | Mutation (MP-X) |
| Safe shutdown | Retirement |

Persistent state:

- Genomes: `governance/subsystem_genomes/*.genome.v1.json`
- Audit: `.runtime/governance/*_audit.jsonl`
- Retirement state: `.runtime/governance/retirement/<gene>.json`
- Backups: `.runtime/governance/promotion_backups/`, `mutation_backups/`

## 1. Alt-4 activation sequence

End-to-end path from summon to live runtime enforcement:

| Step | Action | Command / hook |
|------|--------|----------------|
| 1 | SSP summon (Step 7) writes genome at `concept` | `.cursor/skills/subsystem-summoner/SKILL.md` |
| 2 | Registry validation | `make genome-gate` |
| 3 | Boot validation | `Alt4Runtime.boot_validate()` in `src/api.py`, `app/main.py` |
| 4 | Call-time enforcement | `GenomeEngine.assert_gene_callable(..., stage_min="mvp")` in capability bridge |
| 5 | Composite CI gate | `make alt4-gate` (or `make alt4-gate-strict` to fail on pending promotions) |
| 6 | Stage promotion | `make promotion-apply` |

### Boot environment variables

| Variable | Values | Effect |
|----------|--------|--------|
| `AAIS_GENOME_BOOT` | `fail` (default), `warn`, `skip` | Boot abort vs warn on invalid registry |
| `AAIS_REPO_ROOT` | path | Override repo root (tests, CI) |
| `AAIS_RUNTIME_DIR` | path | Override `.runtime` location |
| `AAIS_ALT4_GATE_STRICT` | `1`, `true` | Fail `alt4-gate` when promotions are pending |

Activation order metadata lives in each genome: `activation.order`, `batch_id`, `notes`.
Retirement sets `activation.order = -1`.

## 2. Promotion Engine

There is **no daemon loop**. Each invocation runs one batch pass over the registry.

```text
scan_all(apply?)
  for each gene in sorted(registry):
    evaluate(gene)     # gates + file checks
    if apply and passed:
      apply(decision)  # backup → genome → LOGBOOK → post genome-gate
```

### Stage machine

```text
concept → prototype → mvp → governed
```

| Target | Checks |
|--------|--------|
| prototype | `ssp-gate`; isolated `runtime.surface` entries |
| mvp | per-gene gate; proof bundles on disk |
| governed | gene gate + `genome-gate`; invariant tests; lineage cross-ref; lifecycle contracts |

### Commands

```bash
make promotion-scan
make promotion-apply
python3 -m src.governance_organs.promotion_engine --gene recipe_module
python3 -m src.governance_organs.promotion_engine --gene recipe_module --apply --dry-run
```

### Failure modes

- Gate subprocess timeout (600s) or missing `make` → evaluate fails
- Missing proof bundle → blocked at mvp/governed
- Post-apply `genome-gate` failure → automatic rollback from backup
- Gene at terminal promotable stage → no-op

Audit: `.runtime/governance/promotion_audit.jsonl`

## 3. Retirement Engine

Contract: [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md)

### 10 steps

```text
mark_deprecated_in_spec → freeze_schema → freeze_api_doc → logbook_entry
→ move_docs_to_retired → genome_deprecated → summon_ineligible
→ activation_order_removed → shim_optional → code_removal_gated
```

State: `.runtime/governance/retirement/<gene>.json`

**Lineage gate:** retirement blocked if any genome lists this gene in `lineage.parents`
without `retirement.migration_proof` on the dependent.

**Code removal (step 10):** never automatic — blocked until shim + two stable releases.

### Commands

```bash
make retirement-scan
make retirement-apply GENE=narrative_trust_pack STEP=6
python3 -m src.governance_organs.retirement_engine --gene narrative_trust_pack
python3 -m src.governance_organs.retirement_engine --gene narrative_trust_pack --apply --step 6
```

Audit: `.runtime/governance/retirement_audit.jsonl`

## 4. Mutation Engine (MP-X)

Contract: [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md)

```text
MP-X proposal → verify (genome-gate + delta + tests) → apply → optional rollback
```

| Artifact | Location |
|----------|----------|
| Proposal | `docs/_future/mutations/MP-*.md` |
| Schema delta | `schemas/deltas/<gene>_<MP-ID>.json` |
| Tests | `tests/test_<gene>_mutation_<MP_ID>.py` |
| Golden example | `MP-NTP-001` for `narrative_trust_pack` |
| Lane mutation golden path | `MP-ALO-001` for `adaptive_lane_organ` |
| Coherence fabric golden path | `MP-OCCF-001` for `operator_cognition_coherence_fabric` |
| Profile organ golden path | `MP-OPO-001` for `operator_profile_organ` |

### Commands

```bash
make coherence-fabric-mutation-gate
make operator-profile-mutation-gate
make narrative-trust-pack-mutation-gate
make adaptive-lane-mutation-gate
python3 -m src.governance_organs.mutation_engine --gene narrative_trust_pack --mp-id MP-NTP-001 --verify
python3 -m src.governance_organs.mutation_engine --gene narrative_trust_pack --mp-id MP-NTP-001 --apply --invariant "Alt-4 Mutation Engine may append governance invariants via MP-X"
python3 -m src.governance_organs.mutation_engine --gene narrative_trust_pack --mp-id MP-NTP-001 --rollback
python3 -m src.governance_organs.mutation_engine --gene adaptive_lane_organ --mp-id MP-ALO-001 --verify
python3 -m src.governance_organs.mutation_engine --gene adaptive_lane_organ --mp-id MP-ALO-001 --apply --invariant "Lane DNA mutations require MP-X, fabric re-validation, and post-apply wake"
python3 -m src.governance_organs.mutation_engine --gene adaptive_lane_organ --mp-id MP-ALO-001 --rollback
python3 -m src.governance_organs.mutation_engine --gene operator_cognition_coherence_fabric --mp-id MP-OCCF-001 --verify
python3 -m src.governance_organs.mutation_engine --gene operator_cognition_coherence_fabric --mp-id MP-OCCF-001 --apply --invariant "Coherence fabric genome mutations require MP-X and post-apply alt7-governed-gate"
python3 -m src.governance_organs.mutation_engine --gene operator_cognition_coherence_fabric --mp-id MP-OCCF-001 --rollback
python3 -m src.governance_organs.mutation_engine --gene operator_profile_organ --mp-id MP-OPO-001 --verify
python3 -m src.governance_organs.mutation_engine --gene operator_profile_organ --mp-id MP-OPO-001 --apply --invariant "Profile authority changes require MP-X and post-apply alt7-governed-gate"
python3 -m src.governance_organs.mutation_engine --gene operator_profile_organ --mp-id MP-OPO-001 --rollback
```

History entries use `proposal_id` (MP-X id) and `status` per genome meta-schema.

Audit: `.runtime/governance/mutation_audit.jsonl`

## Operator quick reference

| Goal | Command |
|------|---------|
| Validate all genomes | `make genome-gate` |
| Boot-safe check | `python3 -c "from src.governance_organs import Alt4Runtime; Alt4Runtime.boot_validate()"` |
| CI composite gate | `make alt4-gate` |
| Strict CI gate | `make alt4-gate-strict` |
| See promotion blockers | `make promotion-scan` |
| Auto-promote eligible genes | `make promotion-apply` |
| Verify MP-X | `make narrative-trust-pack-mutation-gate` or `make adaptive-lane-mutation-gate` |
| Dry-run retirement (all genes) | `make retirement-scan` |
| Full organ test suite | `python3 -m pytest tests/test_governance_organs_alt4.py -q` |

## Related contracts

- [AAIS_SSP_PROMOTION_PROTOCOL.md](./AAIS_SSP_PROMOTION_PROTOCOL.md)
- [AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md](./AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md)
- [AAIS_SUBSYSTEM_MUTATION_PATH.md](./AAIS_SUBSYSTEM_MUTATION_PATH.md)
- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md)
