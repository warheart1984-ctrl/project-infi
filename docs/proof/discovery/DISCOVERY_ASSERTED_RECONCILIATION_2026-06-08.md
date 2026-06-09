# Discovery corpus asserted reconciliation — 2026-06-08

Status: **proven** (manifest + promotion dry-run + catalog render)

## Claim

Every **library-admitted asserted** row in `DISCOVERY_DOCUMENT_MANIFEST.json` carries an explicit `standing_reason` and `promotion_rule`. No ambiguous asserted rows remain without documented standing.

## Standing summary

| `claim_label` | Count | Library admitted |
|---------------|------:|------------------|
| hypothetical | 5 | 13 total admitted |
| asserted | 8 | (subset of admitted) |
| denied | 19 | excluded from library |

## Asserted library entries (8)

| Slug | `promotion_rule` | Decision |
|------|------------------|----------|
| `aais_a_conceptual_architecture_for_governed_cognitive_systems` | `asserted:conceptual_architecture` | Remains **asserted** — conceptual architecture without paired formal science verification |
| `aais_voss_unified_canonical_state_schema` | `asserted:architecture_spec` | Remains **asserted** — architecture/spec patterns only; dual-pattern proof not recorded |
| `architectural_hyper_systemizer_formal_specification_v2_0` | `asserted:architecture_spec` | Remains **asserted** — same |
| `nova_cortex_a_constitutional_runtime_composed_cognitive_architecture_for_synthetic_minds` | `asserted:conceptual_architecture` | Remains **asserted** — conceptual |
| `proof_of_subsystem_a_cryptographically_anchored_subsystem_discovery_mechanism_for_governed_cognitive_runtime_architectur` | `asserted:architecture_spec` | Remains **asserted** — architecture/spec only |
| `the_voss_binding_unified_runtime_calculus` | `asserted:architecture_spec` | Remains **asserted** — architecture/spec only |
| `urg_architecture_a_governed_cognitive_infrastructure_for_multi_tenant_constitutional_ai_systems` | `asserted:conceptual_architecture` | Remains **asserted** — conceptual |
| `multi_model_orchestration_pattern` | `asserted:architecture_spec` | Remains **asserted** — orchestration pattern doc; not dual-pattern promoted |

**None** of the eight rows were promoted to **proven** in this pass — promotion policy v2 requires architecture **and** science pattern evidence. Each row documents why it stays asserted.

## Denied / excluded (19)

Promotion dry-run (`promote_discovery_documents.py --dry-run`) would exclude 19 entries under deny rules (grant proposals, operator narrative, conlang, speculative physics, etc.). These rows already carry `claim_label: denied` and `library_admitted: false`.

## Reproduction

```powershell
py -3.12 tools/governance/promote_discovery_documents.py --dry-run
py -3.12 tools/governance/render_discovery_catalog.py
```

Verify every asserted + library-admitted document has `standing_reason`:

```powershell
py -3.12 -c "import json; m=json.load(open('docs/proof/discovery/DISCOVERY_DOCUMENT_MANIFEST.json')); bad=[d['slug'] for d in m['documents'] if d.get('claim_label')=='asserted' and d.get('library_admitted') and not d.get('standing_reason')]; print('missing', bad or 'none')"
```

Expected: `missing none`

## Gate

Phase 2 plan gate: **0 ambiguous asserted rows** — satisfied.
