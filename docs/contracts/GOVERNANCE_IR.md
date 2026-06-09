# Governance IR Contract

Status: **active contract**

## Purpose

Governance IR is the single law snapshot at one clock tick. The invariant compiler lowers IR into runtime artifacts (check graphs, rollback policies, escalation hooks, ingress plans, mask specs, training views).

## Schema (v1)

```json
{
  "ir_version": "aais.governance_ir.v1",
  "clock_tick_id": "bridge-fingerprint-or-session-turn",
  "compiled_at": "ISO-8601 UTC",
  "ir_fingerprint": "sha256-canonical-json-16",
  "authority_envelope": {
    "principal": {
      "actor_id": "string",
      "session_id": "string|null",
      "tenant_id": "string|null",
      "standing_label": "denied|hypothetical|asserted|proven"
    },
    "resources": ["repo", "session:...", "federation:..."],
    "allowed_verbs": ["observe", "respond", "propose", "execute"],
    "capabilities": ["proposal_only", "governed_llm", "effectful_execution"],
    "delegation_depth": 0,
    "max_subagent_depth": 3
  },
  "invariant_set": {
    "hard": ["packet_shape_complete", "..."],
    "conditional": [
      {"name": "approval_state_declared", "predicate": "requires_approval"}
    ],
    "stage_linked": {
      "concept": ["ingress_protocol_checked"],
      "implementation": ["governed_llm_proposal_required"],
      "verification": ["verification_alignment_required"]
    }
  },
  "execution_context": {
    "cisiv_stage": "implementation",
    "otem_level": "none|detected|approved|blocked",
    "otem_boundary": {},
    "subagent_lineage": [{"bridge_id": "...", "mission_id": "..."}],
    "odl_anchor": {
      "decision_id": "string|null",
      "causal_parents": ["..."],
      "scope_id": "string|null"
    },
    "numeric_otem_level": 10,
    "authority_band": "autonomous|governed|containment|sovereign",
    "containment_mode": false
  },
  "otem_ceiling_rules": {
    "ceiling_version": "aais.otem_ceiling.v1",
    "authority_band": "governed",
    "numeric_level": 10,
    "ceiling_active": false,
    "containment_mode": false,
    "activation_triggers": [],
    "constitutional_law": ["human_principal_root", "fail_closed", "..."],
    "mutable_policy_refs": ["authority_mask_spec", "hardening_thresholds", "..."],
    "operator_unavailable_policy": {"timeout_minutes": 30, "fallback": "quarantine_archive"},
    "pipeline_state": "idle|diagnostic|preview|awaiting_decision|closing_ledger",
    "odl_root_id": "string|null"
  },
  "law_registry": {
    "constitutional": [{"law_id": "fail_closed", "law_class": "constitutional", "amendment_required": true}],
    "mutable": [{"law_id": "authority_mask_spec", "law_class": "mutable", "amendment_required": false}]
  }
}
```

## Source mapping

| IR field | Source |
|----------|--------|
| `clock_tick_id` | `governance_packet.packet_fingerprint` or `bridge_result.bridge_id` + payload hash |
| `authority_envelope.principal` | `authority_snapshot`, session metadata, UGR standing |
| `authority_envelope.resources` | bridge payload `session_id`, `trace_id`, workspace scope |
| `authority_envelope.allowed_verbs` | `execution_intent`, effectful flag, packet type |
| `authority_envelope.capabilities` | governed LLM module, effectful execution, proposal-only default |
| `invariant_set.*` | `cognitive_bridge._derive_invariants` output, classified |
| `execution_context.cisiv_stage` | `chat_turn_governance.infer_chat_turn_cisiv_stage` or payload |
| `execution_context.otem_*` | `api._build_otem_boundary_snapshot`, approval bridge |
| `execution_context.subagent_lineage` | bridge `runtime_context`, UGR `mission_id` chain |
| `execution_context.odl_anchor` | `operator_decision_ledger` active node projection |
| `execution_context.numeric_otem_level` | `src/otem_capability.get_otem_capability_level()` |
| `execution_context.authority_band` | `src/otem_capability.authority_band()` |
| `execution_context.containment_mode` | `src/otem_ceiling.OtemCeilingController` state |
| `otem_ceiling_rules` | `src/otem_ceiling.rules_for_ir()` |
| `law_registry` | `src/otem_ceiling.default_law_registry()` |

## Constitutional vs mutable law

Governance IR carries a **law registry** split for the OTEM Level 20 ceiling:

- **Constitutional** entries cannot be overridden at sovereign recovery (level 20) without an explicit `constitutional_amendment` ODL decision kind.
- **Mutable** entries (masks, hardening thresholds, escalation/admission rules) may be reset or narrowed within constitution during recovery.

Normative ceiling rules: [`OTEM_CEILING_RULES.md`](OTEM_CEILING_RULES.md). Schema: `schemas/otem_ceiling_rules.v1.json`.

## Builder

- Module: `src/governance_ir.py`
- Entry: `build_governance_ir(bridge_result=..., authority_snapshot=..., standing=..., runtime_context=..., odl_anchor=...)`
- Fingerprint: canonical JSON sha256, first 16 hex chars (matches cognitive bridge style).

## Shared vocabulary

Governance IR fields (`allowed_verbs`, `invariant_set.stage_linked`, `execution_context.cisiv_stage`, `execution_context.otem_level`) are lowered using the canonical taxonomy in [`GOVERNANCE_TAXONOMY.md`](GOVERNANCE_TAXONOMY.md).

- Module: `src/governance_taxonomy.py`
- Schema: `nova.governance_taxonomy.v1`
- Consumers: `src/authority_mask_lowering.py`, `src/training_view_spec.py`, `src/invariant_compiler.py`

Mask and training artifacts for the same IR share `ir_fingerprint` and `taxonomy_fingerprint` from this vocabulary.

## Fail-closed

Missing required bridge fields → builder raises `GovernanceIRValidationError`. Compiler errors mirror bridge invariant block semantics.
