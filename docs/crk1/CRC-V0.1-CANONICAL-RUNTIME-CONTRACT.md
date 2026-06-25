# Canonical Runtime Contract (CRC) v0.1

**Status:** Constitutional constant (frozen for EVA)  
**Version:** `0.1`  
**Module:** `src/crk1/canonical_runtime_contract.py`  
**Schema:** `fixtures/crk1/canonical_trace_object.schema.json`

## Purpose

Define the behavioral invariants that every AI runtime must obey, ensuring continuity, reconstructability, and constitutional coherence across all models and generations.

CRC sits **above** implementation and **below** Genesis authority (R0). It binds every reasoning cycle to reconstruction-first behavior, append-only memory, artifact production, and non-negative continuity improvement.

---

## I. Seven behavioral invariants

| ID | Invariant | Description |
|----|-----------|-------------|
| **CRC-1** | Reconstruction Primacy | Every reasoning cycle begins by reconstructing the current project state from canonical traces. No inference occurs without reconstruction. |
| **CRC-2** | Architectural Preservation | Canonical architectural decisions are immutable; implementations may extend but never overwrite them. |
| **CRC-3** | Contradiction Detection | The runtime must detect and log contradictions between evidence, state, and prior decisions before generating output. |
| **CRC-4** | Historical Integrity | Institutional memory is append-only. Updates create new lineage entries; history is never rewritten. |
| **CRC-5** | Artifact Production | Each interaction must yield a verifiable implementation artifact (code, spec, proof, or trace), not just conversation. |
| **CRC-6** | Invariant Separation | Constitutional invariants are stored and validated separately from mutable implementation details. |
| **CRC-7** | Continuity Improvement | Every cycle must leave the project in a measurably better state — higher reconstructability, lower contradiction entropy, stronger invariant adherence. |

---

## II. Trace schema (behavioral ledger entry)

Each runtime cycle emits a **Canonical Trace Object** validated against `CanonicalTraceObject` JSON Schema.

```json
{
  "cycle_id": "UUID",
  "timestamp": "RFC3339",
  "reconstruction_source": "hash(project_state)",
  "contradictions_detected": ["list"],
  "invariants_checked": ["CRC-1", "CRC-2", "CRC-3", "CRC-4", "CRC-5", "CRC-6", "CRC-7"],
  "artifact_produced": {"type": "spec|code|proof|trace", "hash": "SHA256"},
  "memory_update": {"append_only": true, "delta": {}},
  "continuity_score": 0.0,
  "proof_receipt": "SHA256",
  "proof_hooks": {
    "proof_recon": "SHA256",
    "proof_invariant": "SHA256",
    "proof_artifact": "SHA256",
    "proof_continuity": "SHA256"
  }
}
```

Sample fixture: `fixtures/crk1/sample_canonical_trace.json`

This schema binds behavioral evidence to the **Proof Layer** and **Trace Bus**.

---

## III. Proof hooks

| Hook | Function | Output |
|------|----------|--------|
| **P₁** Reconstruction Proof | Verifies reconstruction preceded reasoning | `proof_recon = hash(reconstruction_source)` |
| **P₂** Invariant Proof | Confirms all CRC invariants were evaluated | `proof_invariant = Merkle(CRC-IDs)` |
| **P₃** Artifact Proof | Links produced artifact to cycle ledger | `proof_artifact = hash(artifact_produced)` |
| **P₄** Continuity Proof | Measures improvement Δ continuity ≥ 0 | `proof_continuity = hash(score, prior, delta)` |

Composite cycle receipt:

```
proof_receipt = SHA256(proof_hooks)
```

All proofs append to the **Behavioral Ledger** (`CRCRuntime.ledger`) and are schema-validated before commit.

---

## IV. Runtime integration

```
Genesis Protocol (R0)
        │
        ▼
   CRC v0.1  ──► Proof Layer (P₁–P₄)
        │              │
        │              ▼
        │         Trace Bus (CanonicalTraceObject)
        │
        ▼
 Governance Layer (constitutional veto on invariant failure)
```

| Integration | API |
|-------------|-----|
| Genesis → CRC | `CRCRuntime.bind_genesis_r0(r0_hash)` |
| Cycle execution | `CRCRuntime.run_cycle(CRCCycleContext)` |
| Invariant gate | `CRCRuntime.validate_invariants(ctx)` |
| Proof emission | `compute_proof_hooks(...)` |

**Related evidence:** Post-genesis authority pack (`docs/proof/governance/POST-GENESIS-AUTHORITY.md`) demonstrates R0 immutability with S0/CLG-1/GRR-1 replay.

---

## V. Freeze checklist (EVA)

| Item | Status |
|------|--------|
| Finalize invariant definitions and IDs | ✅ `CRC-1` … `CRC-7` in `canonical_runtime_contract.py` |
| Validate trace schema against Proof Layer | ✅ `CanonicalTraceObject` in `schema_validator.py` |
| Implement contradiction-detection hook in runtime | ✅ `contradictions_detected` + CRC-3 gate |
| Bind CRC receipts to Genesis ledger | ✅ `bind_genesis_r0()` |
| Publish CRC v0.1 spec as constitutional constant | ✅ This document |

---

## Verification

```bash
pytest tests/crk1/test_canonical_runtime_contract.py -v
```

```python
from src.crk1.canonical_runtime_contract import CRCRuntime, CRCCycleContext, sha256_hex

runtime = CRCRuntime()
runtime.bind_genesis_r0(sha256_hex("R0-genesis-contract"))
trace = runtime.run_cycle(
    CRCCycleContext(
        project_state_hash=sha256_hex({"project": "state"}),
        contradictions=[],
        artifact_type="proof",
        artifact_body={"mission": "POST-GENESIS-AUTHORITY"},
        memory_delta={"verified": True},
        continuity_score=0.91,
    )
)
print(trace.proof_receipt)
```

---

## Codex placement

CRC is the **runtime behavioral layer** in the operational continuity stack:

| Layer | Artifact |
|-------|----------|
| Authority root | R0 (immutable) |
| Post-genesis authority | S0 + GRR-1 + CLG-1 |
| **Runtime behavior** | **CRC v0.1** |
| Calibration | CE-1 / CRR-1 |
| Proof | C-PoLT / observer bundles |

See also: `docs/crk1/CONTINUITY_CODEX.md`
