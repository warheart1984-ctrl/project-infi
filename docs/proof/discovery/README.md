# Proof-of-Discovery artifacts

Governed evidence packets registered for UGR contribution discovery (`contribution_type: proof`).

## Corpus status

| Metric | Count |
|---|---|
| Documents in manifest | 32 |
| **Library admitted** | 13 (5 hypothetical + 8 asserted) |
| **Asserted (library)** | 8 — each has explicit `standing_reason` in manifest |
| **Denied** | 19 (promotion policy excludes) |

Reconciliation (2026-06-08): [DISCOVERY_ASSERTED_RECONCILIATION_2026-06-08.md](./DISCOVERY_ASSERTED_RECONCILIATION_2026-06-08.md) — **0 ambiguous asserted rows** (each asserted entry is proven-path or documented deny reason).

Authoritative inventory: **`DISCOVERY_DOCUMENT_MANIFEST.json`**

Rendered catalog (regenerate with `py -3.12 tools/governance/render_discovery_catalog.py`): **`_catalog_table.md`**

Trust bundle for the bulk corpus: `docs/trust_bundles/OPERATOR_DOCUMENT_CORPUS_DISCOVERY_TRUST_BUNDLE.md`

## Discovery Pods

Every pod display name is recorded in the append-only ledger **`discovery-pods.jsonl`**. On successful contribution discovery, the system **evaluates admission policy** (`deploy/ugr/discovery-pod-admission.json`) before registering a **new** pod: proven contributions, explicit pod fields (unless `UGR_POD_EXPLICIT_REQUIRES_RECEIPT=1`), and high-value contribution types with a verified signed receipt qualify automatically; low-signal discoveries are skipped (`discovery_pod_ledger.skip_reason`). Proven `capability` / `substrate` types can admit via `admit_deferred_types_when_proven`. Already-registered pods always receive `pod_discovered` events. The same policy applies to **subsystem-only** discovery (`spec` payload route) and unified contribution discovery. Tune strictness with `UGR_POD_MIN_INVARIANT_PASS_COUNT` (overrides policy `min_invariant_pass_count`). Admission skip/admit reasons are counted in-process for ops (`pod_admission_metrics`). The registry **`deploy/ugr/discovery-pods.json`** refreshes with discovery and proven totals, including **`governance_arc_tier`** and **`pod_reward_multiplier`** when High or Civilizational arc metadata is present. The first pod is **Jon Halstead** (`pod:jon-halstead`, `operator:jon-halstead`).

Discovery responses include `discovery_pod_ledger` with pod id, `admission` verdict (when evaluated), discovery count, and whether the pod was newly registered. When `claim_label` is **`proven`**, reputation and rail credits are **persisted automatically** even if `UGR_REWARDS_SHADOW_ONLY=1` (override via `UGR_REWARDS_PROVEN_PERSIST=0` to disable). **High** and **Civilizational** arc contributions apply a **10×** pod reward multiplier (default 18 → 180 reputation for proof). The pod ledger also appends a `pod_proven` event and refreshes proven reputation totals on the registry.

Manual registration (optional):

```bash
py -3.12 -m src.ugr.discovery.discovery_pod_ledger register "Display Name" --label "Optional label"
```

List all ledger entries:

```bash
py -3.12 -m src.ugr.discovery.discovery_pod_ledger list
```

## Layout

| Path | Purpose |
|---|---|
| `DISCOVERY_DOCUMENT_MANIFEST.json` | Canonical index of all registered documents (SHA256, claim label, contribution id, receipt path) |
| `_catalog_table.md` | Human-readable table generated from the manifest |
| `discovery-pods.jsonl` | Append-only ledger of every pod name registered |
| `packets/` | Proof packets for bulk-registered PDFs (`*_DISCOVERY_PROOF.md`) |
| `receipts/` | UGR contribution discovery receipts (`*_discovery_receipt.json`) |
| `SIX_INVARIANTS_DISCOVERY_PROOF.md` | Canonical **proven** proof packet for Six Invariants |
| `The_Six_Invariants.pdf` | Canonical source PDF (also referenced by proven registration) |
| `six_invariants_discovery_receipt.json` | Receipt for the proven Six Invariants registration |

Source PDFs remain at their original paths (repo root and `docs/fieldguide/`). Proof packets reference those paths; they are not copied into this folder.

## Pattern-based promotion (asserted ↔ proven)

Claim labels are resolved automatically from **`deploy/ugr/discovery-proof-promotion.json`** v2 (`src/ugr/discovery/proof_promotion.py`).

**Proven** requires **both**:

1. **Architecture** — governed cognitive / constitutional runtime / AAIS / URG / Nova Cortex / Hyper-Systemizer / Voss / subsystem discovery, etc.
2. **Science** — formal theory or specification, invariants, calculus, cryptographic anchoring, canonical state schema, etc.

**Exceptions:** manifest entries flagged `canonical` (Six Invariants) are always **proven**.

**Denied** (stay **asserted**): grant proposals, LinkedIn/case studies, DARPA/concept pitches, research concepts, industrial tangents, speculative physics, conlang, operator narratives (primers, taxonomia, profiles, accelerators), and manifests flagged `duplicate_of`.

Reconcile the manifest (promote **and** demote when policy changes):

```bash
set UGR_SUBSYSTEM_DISCOVERY_ENABLED=1
py -3.12 tools/governance/promote_discovery_documents.py
```

Preview without UGR calls:

```bash
py -3.12 tools/governance/promote_discovery_documents.py --dry-run
```

Override policy path: `UGR_DISCOVERY_PROOF_PROMOTION_POLICY_PATH`. Force a single label for all new docs: `--claim-label proven|asserted` (disables auto-promote on register).

## Bulk registration

Register all operator PDFs (repo root + `docs/fieldguide/`). Default: **auto-promote** via patterns; re-run **upgrades** existing asserted rows that now match proven rules:

```bash
set UGR_SUBSYSTEM_DISCOVERY_ENABLED=1
py -3.12 tools/governance/register_discovery_documents.py
```

Dry run (writes packets only, no UGR calls):

```bash
py -3.12 tools/governance/register_discovery_documents.py --dry-run
```

Disable pattern resolution: `--no-auto-promote`. Skip upgrading existing asserted entries: `--no-upgrade-existing`.

Idempotent: re-running skips documents already present in the manifest (matched by SHA256). `The_Six_Invariants.pdf` under this directory is skipped because it is covered by the canonical proven entry.

## Single-document API registration

Register via `POST /api/ugr/discover/contribution` with:

```json
{
  "tenant_id": "global",
  "operator_id": "operator:jon-halstead",
  "aais_instance_id": "aais-primary",
  "contribution_type": "proof",
  "payload": {
    "proof_path": "docs/proof/discovery/SIX_INVARIANTS_DISCOVERY_PROOF.md",
    "claim_label": "proven",
    "discovery_pod_id": "pod:jon-halstead"
  }
}
```

## Document catalog

Full table (31 rows, regenerated from manifest): **`_catalog_table.md`**

Canonical **proven** entry: `SIX_INVARIANTS_DISCOVERY_PROOF.md` / `The_Six_Invariants.pdf`.

Documents that remain **asserted** (deny rules, duplicate flag, or architecture/science AND not satisfied):

| Title | Why asserted |
|---|---|
| Anchor_Connectome_Framework_Grant_Proposal_v2_1 | grant proposal deny |
| SEA-FORGE (cultured meat / 3D food) | industrial tangent deny |
| The LinkedIn Lockout — case study | LinkedIn / case study deny |
| The Six Invariants (root duplicate PDF) | `duplicate_of: six_invariants` |
| WOLF‑1 DARPA-style concept white paper | concept pitch deny |
| Goblin primers, taxonomia, field editions | operator narrative deny |
| AAIS / Nova Cortex / URG (conceptual only) | architecture without formal science |
| Formal theory / Law of Duality (standalone) | science without governed architecture |

The root copy of *The Six Invariants* (long filename) is byte-identical to `The_Six_Invariants.pdf` and is tagged `duplicate_of: six_invariants` in the manifest.

Contract: `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
