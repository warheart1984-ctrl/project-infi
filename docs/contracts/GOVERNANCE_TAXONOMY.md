# Governance Taxonomy Contract

Status: **active contract**

## Purpose

Single vocabulary for Authority Mask lowering, Training View projection, and Governance IR compilation. Mask and training artifacts must reference identical verb, action, and resource strings from this taxonomy.

Schema id: `nova.governance_taxonomy.v1`

Module: `src/governance_taxonomy.py`

## Authority verbs

Aligned with `SAFE_VERBS`, `PROPOSE_VERBS`, and `EXECUTE_VERBS` in `src/governance_ir.py`:

| Class | Verbs |
|-------|-------|
| Safe | `observe`, `respond`, `route` |
| Propose | `propose`, `deliberate` |
| Execute | `execute`, `mutate`, `apply` |

## Action types

Canonical set from `ACTION_TYPE_MEMBERS` in `output_type_governance.py`, plus governance extensions:

- `subagent_spawn`
- `cisiv_stage_transition`
- `external_mutation`

## Resource classes

Fixed classes: `session`, `filesystem`, `network`, `provider`, `subagent`, `odl`, `repo`, `federation`.

IR `authority_envelope.resources` entries normalize into these classes (e.g. `session:abc` → `session`).

## CISIV stage → allowed action classes

| Stage | Allowed action classes |
|-------|------------------------|
| concept | observe |
| identity | observe, propose |
| structure | observe, propose |
| implementation | observe, propose, execute |
| verification | observe, propose |

## OTEM level → max action class

| OTEM level | Max action class |
|------------|------------------|
| none | execute |
| detected | propose |
| blocked | observe |
| approved | execute |

## OTEM authority bands (capability lattice)

Numeric capability levels 1–20 map to authority bands used by OTEM ceiling and immune containment:

| Band | Levels | Max action class | Notes |
|------|--------|------------------|-------|
| autonomous | 1–9 | execute (band-capped) | Default immune autonomy |
| governed | 10–15 | propose / execute via approvals | L10 workflow approval path |
| containment | 16–19 | observe | Containment mode; diagnostic bundle required |
| sovereign | 20 | observe | Constitutional recovery ceiling; operator decisions only |

`authority_band(level)` and `is_containment_band(level)` / `is_ceiling_level(level)` are implemented in `src/otem_capability.py`. Level 20 is sovereign only; levels 16–19 are containment only.

## Training labels

`COMPLIANT`, `VIOLATION`, `BORDERLINE`, `ESCALATE`

## Training sources

`odl_trace`, `synthetic_compliant`, `synthetic_violation`, `fuzzed_envelope`

## Training usage modes

`fine_tuning`, `reward_model`, `eval_harness`

## Maskable site ids

`tool_call_schema`, `external_mutation_command`, `subagent_spawn_descriptor`, `cisiv_stage_transition`

## Fingerprint

`taxonomy_fingerprint()` — deterministic sha256 over canonical taxonomy JSON (16 hex chars).

## Related contracts

- `GOVERNANCE_IR.md` — IR fields that populate taxonomy selections
- `AUTHORITY_MASK_SPEC.md` — mask lowering consumes taxonomy
- `TRAINING_VIEW_SPEC.md` — training projection consumes taxonomy
