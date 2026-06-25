# Personal continuity runtime

## StateObjects

### IdeaState

| Field | Description |
|-------|-------------|
| `idea_id` | Stable identifier |
| `title` | Human label |
| `status` | `seed`, `in_flight`, `frozen`, `retired` |
| `lineage` | Parent idea IDs |
| `assumptions` | Linked assumption IDs |
| `linked_systems` | System references |
| `evidence_links` | Artifact / receipt IDs |

### AssumptionState

| Field | Description |
|-------|-------------|
| `assumption_id` | Stable identifier |
| `statement` | Text |
| `confidence` | 0–1 or ordinal |
| `status` | `active`, `challenged`, `retired` |
| `supporting_evidence` | Evidence bundle IDs |

### DesignLineageState

| Field | Description |
|-------|-------------|
| `lineage_id` | Stable identifier |
| `root_idea_id` | Root of chain |
| `evolution_chain` | Ordered idea/decision IDs |

### CriticalContextState

“If I disappear tomorrow” — `context_id`, `description`, `dependencies`, `reconstruction_difficulty`.

## Receipts

| Type | Kinds |
|------|-------|
| `IdeaReceiptV2` | Creation, Refinement, Freeze, Retire |
| `AssumptionReceiptV2` | Adopt, Challenge, Retire |
| `LineageReceiptV2` | Link, Fork, Merge |
| `ContinuityRiskReceiptV2` | Observation (e.g. high SPOF risk on idea X) |
| `ContinuityRemediationReceiptV2` | Closure — externalization + lineage linkage |

## Invariants

- **PC-1:** No foundational idea may remain `in_flight` without at least one externalized artifact.
- **PC-2:** No critical assumption may remain implicit once it influences system-level decisions.
- **PC-3:** Every system-critical design must link to at least one `DesignLineageState`.
- **PC-4:** “If I disappear tomorrow” contexts must have an active remediation plan or be explicitly accepted as risk.

## Remediation lifecycle

**Trigger:** `ContinuityRiskReceiptV2` with `risk_score > θ`.

**Path:** Identify gap → Externalize context → Link to artifacts → Recompute risk.

**Closure:** `ContinuityRemediationReceiptV2`.

## Risk model

**Inputs:** implicit assumptions, in-flight foundational ideas, unlinked critical contexts.

**Risk score:** P(key architectural decision unreconstructable without founder).

## Learning model

**Measure:** reduction in founder-only knowledge over time.

**Evidence:** before/after counts of implicit assumptions, unlinked design decisions, critical contexts without artifacts.

## Amendment hooks

Amendments change: what qualifies as “foundational”, externalization thresholds, acceptable continuity risk levels.
