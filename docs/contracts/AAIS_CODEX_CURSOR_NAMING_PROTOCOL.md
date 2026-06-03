# AAIS Codex / Cursor Naming Protocol

Status: **active contract**

CISIV stage: **structure**

Translation contract between mythic cognition (operator intent) and deterministic code engines (Codex, Cursor, CI gates).

## Related contracts

- [AAIS_SSP_PROTOCOL.md](./AAIS_SSP_PROTOCOL.md) — subsystem admission; new admissions follow this protocol
- [AAIS_SUBSYSTEM_GENOME.md](./AAIS_SUBSYSTEM_GENOME.md) — genome `identity.gene` remains snake_case; optional `ssp.engineering_class` documented below
- [.cursor/skills/subsystem-summoner/SKILL.md](../../.cursor/skills/subsystem-summoner/SKILL.md)
- [governance/legacy_engineering_aliases.v1.json](../../governance/legacy_engineering_aliases.v1.json) — Wave 3 alias registry
- Project Infinity terminology: [README.md § Terminology](../../README.md)

---

## 1. Ontology contract

| Layer | Where it lives | Example |
|-------|----------------|---------|
| Mythic name | Comments and docs only | Coherence Fabric |
| Engineering name | Identifiers (class, module stem, public API) | `OperatorCognitionCoherenceLayer` |
| Legacy repo id | Frozen paths (grandfather) | `operator_cognition_coherence_fabric.py` |

Codex and Cursor treat **identifiers as semantic anchors**. Mythic language must not appear in function names, class names, or new file stems.

---

## 2. Subsystem naming pattern (mandatory for new code)

Every new subsystem uses:

```text
<Domain><Function><Role>
```

- **PascalCase** for the primary class name
- **snake_case** module file matching the class stem (Python: `runtime_plane_manager.py` → `RuntimePlaneManager`)

Examples:

| Engineering class | Role hint |
|-------------------|-----------|
| `RuntimePlaneManager` | coordinates runtime planes |
| `GovernanceConstraintEngine` | evaluates governance constraints |
| `ExecutionDepthMonitor` | observes execution depth |

Do **not** invent alternate patterns (e.g. `*_organ`, `summon_wave`, metaphor verbs as symbols).

---

## 3. Function naming

Functions must be **verbs** describing deterministic behavior:

- Good: `propagate_constraints()`, `evaluate_invariants()`, `synchronize_state()`
- Bad: `coherence_fabric()`, `summon_wave()`, `organ_governance()` — mythic; use comments instead

---

## 4. Dual-layer comment protocol

Every class and every public function gets two comment lines minimum:

```python
# Mythic: <short metaphor — operator-native language>
# Engineering: <literal behavior — what the code must do>
```

Add when applicable:

```python
# Invariant: <must-always-hold property>
# Boundary: <what this unit does not do>
```

Example:

```python
# Mythic: The Coherence Fabric — tissue keeping organs aligned.
# Engineering: Distributed constraint propagation for cross-module consistency.
# Invariant: state remains monotonic across propagation steps.
def propagate_constraints(state: dict) -> CoherenceExecuteResult:
    ...
```

---

## 5. File structure

### 5.1 One subsystem per file

Do not combine multiple conceptual subsystems in one module.

### 5.2 File header (new and touch-on-edit)

Every subsystem Python/TS module should begin with:

```python
# Mythic: <subsystem mythic name>
# Engineering: <DomainFunctionRole class name>
# Responsibilities: <bullet-style literal list>
# Non-responsibilities: <explicit exclusions>
# Invariants: <minimal invariant list>
```

Template: [.cursor/skills/subsystem-summoner/templates/python_subsystem_header.py](../../.cursor/skills/subsystem-summoner/templates/python_subsystem_header.py)

---

## 6. Architectural directives (Codex/Cursor-safe)

1. Never describe behavior only metaphorically — always pair mythic + engineering text.
2. State **invariants** explicitly; agents respect invariants over prose.
3. State **boundaries** (non-responsibilities) so tools do not invent scope.

---

## 7. Prompting rules (Jon Safety Net)

When prompting Codex or Cursor:

1. Give the **engineering name first**, then optional mythic name.
2. Always specify: **inputs**, **outputs**, **constraints**, **failure modes**.
3. Whenever you use a mythic description, also supply: engineering translation, invariants, boundaries.

---

## 8. Grandfather clause

The following are **frozen** unless an approved MP-X mutation and genome-gate pass:

- Existing `src/**/*_organ.py` and `src/**/*_fabric.py` paths
- Existing `governance/subsystem_genomes/*.genome.v1.json` filenames
- Existing `MODULE_ID = "AAIS-*"` values

New SSP admissions **must not** create new `*_organ.py` or `*_fabric.py` filenames. Use engineering module stems and dual-layer headers instead.

Standard language mapping (unchanged): see [README.md § Terminology](../../README.md).

---

## 9. Migration waves

| Wave | When | Action |
|------|------|--------|
| **0** | Contract + rules + SSP | This document; `.cursor/rules/jon-*.mdc`; skill templates |
| **1** | Ongoing | New subsystems: engineering names only; no new organ/fabric stems |
| **2** | Touch-on-edit | Legacy files: add file header + dual comments; keep path and `MODULE_ID` |
| **3** | Registry | [legacy_engineering_aliases.v1.json](../../governance/legacy_engineering_aliases.v1.json) for comment/doc tooling |
| **4** | Explicit MP-X only | Per-subsystem path rename + genome update + `make genome-gate` |

---

## 10. Genome documentation field (pre-schema)

Until `identity.engineering_class` is added to [subsystem_genome.v1.json](../../schemas/subsystem_genome.v1.json), concept-stage genomes may include under `ssp`:

```json
"ssp": {
  "engineering_class": "RuntimePlaneManager",
  "mythic_label": "Runtime plane steward"
}
```

`identity.gene` stays snake_case for gate compatibility.

---

## 11. Legacy alias appendix (representative)

Full registry: [governance/legacy_engineering_aliases.v1.json](../../governance/legacy_engineering_aliases.v1.json).

| Legacy gene / path stem | Engineering class (comments & new code) | Mythic label |
|-------------------------|----------------------------------------|--------------|
| `operator_cognition_coherence_fabric` | `OperatorCognitionCoherenceLayer` | Coherence Fabric |
| `project_infi_law_organ` | `ProjectInfiLawEngine` | Law substrate |
| `mystic_engine_organ` | `MysticEngineBridge` | Mystic engine |
| `forensic_triangulation_organ` | `ForensicTriangulationEngine` | Triangulation ledger |
| `genome_engine` | `GenomeValidationEngine` | Genome DNA validator |
| `coherence_projection_organ` | `CoherenceProjectionLayer` | Coherence projection |

---

## 12. Linguistic genome (naming-genome-gate)

Cross-layer validation of mythic and engineering text across genomes, alias registry, source headers, and concept specs.

```bash
make naming-genome-gate          # warn mode; writes snapshots on fingerprint change
make naming-genome-gate-strict   # errors on missing SSP linguistic fields
python tools/governance/backfill_naming_genome.py --write  # one-time SSP backfill
```

Required SSP fields (after backfill):

| Field | Purpose |
|-------|---------|
| `ssp.engineering_class` | PascalCase `<Domain><Function><Role>` |
| `ssp.mythic_label` | Short mythic name for operator docs |
| `ssp.linguistic_version` | Bump on MP-X mythic/engineering changes (e.g. `1.0.0`) |

Snapshots: [governance/linguistic_snapshots/](../../governance/linguistic_snapshots/) — schema [linguistic_snapshot.v1.json](../../schemas/linguistic_snapshot.v1.json).

Library: [tools/linguistic_genome_lib.py](../../tools/linguistic_genome_lib.py).

---

## 13. Linguistic diff (hybrid history)

Shows how mythic and engineering layers evolve for one gene.

```bash
# Snapshot timeline (latest checkpoints)
python tools/linguistic_diff.py --gene operator_cognition_coherence_fabric

# Git-backed older transitions
python tools/linguistic_diff.py --gene operator_cognition_coherence_fabric --git --since 2026-05-01

# Makefile convenience
make linguistic-diff GENE=operator_cognition_coherence_fabric
```

**Hybrid policy:** snapshot checkpoints from naming-genome-gate first; git log on genome-linked paths fills older gaps.

---

## 15. Waves 5–8 (linguistic stack extensions)

| Wave | Tool | Purpose |
|------|------|---------|
| **5** | `linguistic_mutation_engine` + `apply_linguistic_mutation.py` | MP-X `linguistic_layer` — governed mythic/engineering changes |
| **6** | `mythic_engineering_translator.py` | Deterministic mythic → `<Domain><Function><Role>` for SSP |
| **7** | `linguistic_lineage_viz.py` | Mermaid graph of genome lineage + linguistic labels |
| **8** | `linguistic_drift_predictor.py` | Drift risk score (`low` / `medium` / `high`) from alignment + snapshots |

```bash
make translate-mythic MYTHIC='Runtime plane steward'
make linguistic-mutation-gate
python tools/governance/apply_linguistic_mutation.py --dry-run MP-LING-001 --gene operator_cognition_coherence_fabric
make linguistic-drift-gate
make linguistic-lineage-viz GENE=operator_cognition_coherence_fabric OUTPUT=docs/audit/LINGUISTIC_LINEAGE_GRAPH.md
```

**Drift remediation:** Wave 2 source headers, MP-LING mutation, or re-run translator.

---

## 16. Meta-linguistic governance (Waves 9–10)

Orchestrator: [AAIS_META_LINGUISTIC_GOVERNANCE.md](./AAIS_META_LINGUISTIC_GOVERNANCE.md)

| Wave | Tool | Purpose |
|------|------|---------|
| **9** | `generate_linguistic_remediations.py` | Drift-driven remediation playbooks (no auto-apply) |
| **10** | `linguistic_cascade_report.py` | Lineage cascade impact when parent linguistic layer changes |
| **Meta** | `make meta-linguistic-gate` | Runs naming + naming-genome + linguistic-mutation + linguistic-drift gates |

```bash
make meta-linguistic-gate
python tools/governance/generate_linguistic_remediations.py --min-band medium
make linguistic-remediation-gate
python tools/linguistic_cascade_report.py --gene operator_cognition_coherence_fabric
make linguistic-lineage-viz CASCADE_FROM=operator_cognition_coherence_fabric GENE=operator_cognition_coherence_fabric
```

Registry: [governance/meta_linguistic_registry.v1.json](../../governance/meta_linguistic_registry.v1.json) (`observe` | `enforce`).

---

## 17. Self-optimizing governance cycle (Wave 11)

| Wave | Tool | Purpose |
|------|------|---------|
| **11** | `run_linguistic_governance_cycle.py` | Closed loop: gates → drift → remediations → cascade scan → optimize |

```bash
make linguistic-governance-cycle
make linguistic-governance-cycle-gate
```

Cycle reports: [governance/linguistic_governance_cycles/](../../governance/linguistic_governance_cycles/). Recommendations only — no auto MP-LING apply.

---

## 18. Predictive governance cycle (Wave 12)

| Wave | Tool | Purpose |
|------|------|---------|
| **12** | `run_linguistic_predictive_cycle.py` | Forecast drift before bands escalate; preemptive watch playbooks |

```bash
make linguistic-predictive-cycle
make linguistic-drift-forecast
make linguistic-predictive-gate
```

Run Wave 12 before Wave 11 for full anticipate → react loop. Forecast: [governance/linguistic_drift_forecast.v1.json](../../governance/linguistic_drift_forecast.v1.json).

---

## 19. Calibrating + prescriptive cycle (Wave 13)

| Wave | Tool | Purpose |
|------|------|---------|
| **13** | `run_linguistic_calibration_cycle.py` | Verify forecasts; tune weights (recommendations) |
| **13** | `linguistic_governance_queue.py` | Unified operator backlog |
| **13** | `run_linguistic_full_governance_cycle.py` | Full calibrate → predict → react → queue → gates |

```bash
make linguistic-full-governance-cycle
make linguistic-calibration-cycle
make linguistic-governance-queue
```

---

## 20. Attested closed-loop + work orders (Wave 14)

| Wave | Tool | Purpose |
|------|------|---------|
| **14** | Forecast archive | Same-session calibration via `governance/linguistic_forecast_archive/` |
| **14** | `linguistic_work_order.py` | Operator work-order sync and status |
| **14** | `run_linguistic_attestation.py` | Unified attestation digest + `closed_loop_score` |

```bash
make linguistic-work-order-sync
make linguistic-governance-attestation
make linguistic-attestation-gate
make alt24-gate
```

Full cycle (Wave 14): archive → calibrate (archive-aware) → predict → react → queue → work orders → attestation → gates.

---

## 14. Verification

```bash
make naming-gate
make naming-genome-gate
make meta-linguistic-gate
make ssp-gate
make genome-gate
```

Cursor rules: `.cursor/rules/jon-ontology.mdc`, `jon-dual-comments.mdc`, `jon-file-structure.mdc`, `jon-prompting.mdc`.

---

## TL;DR

Mythic in comments. Engineering in code. Verbs for functions. Explicit invariants. Explicit boundaries. One subsystem per file. Always dual-layer comments. Grandfather legacy organ/fabric paths.
