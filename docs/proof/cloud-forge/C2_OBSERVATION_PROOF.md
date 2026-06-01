# Cloud Forge Phase 2 Proof Packet

Claim: Observation layer — rail-decisions JSONL ledger, promotion stub, EXPRESS domain template, Jarvis readout — is **complete**.

Claim status: **proven** (27 unit tests combined Phase 1+2, Python 3.12, exit 0).

Authority: `docs/contracts/cloud-forge-rail-contract.md`, `docs/contracts/COLLECTIVE_PATTERN_LEDGER.md`.

## Scope

| ID | Deliverable | Path |
|---|---|---|
| C2-1 | Rail decisions JSONL adapter | `src/cloud_forge/ledger.py` → `docs/proof/cloud-forge/rail-decisions.jsonl` |
| C2-2 | Promotion stub | `src/cloud_forge/promotion.py` |
| C2-3 | EXPRESS template `forge/voss/os_architecture` | `src/cloud_forge/templates.py` |
| C2-4 | Jarvis readout | `src/cloud_forge/readout.py`, `src/jarvis_modular.py` |
| C2-5 | Integration | `src/cloud_forge/integration.py` |

## Verification commands

```bash
py -3.12 -m unittest tests.test_cloud_forge_rails tests.test_cloud_forge_phase2 -v
```

## Evidence (2026-05-28)

```
Ran 27 tests in 15.323s

OK
```

## Behaviors proven

- Ledger append/read roundtrip with `task_snapshot`
- `estimate_novelty` → LOW after ≥2 matching ledger rows
- Promotion candidate always `pending_review`; no auto Hall of Fame
- Domain template prefetches constitutional + Cloud Forge docs
- `build_modular_provider_preview` attaches `cloud_forge_readout` when `metadata.cloud_forge_context` set
- Pipeline `cloud_forge_context` uses observed path (template + ledger optional)

## Operator usage

Jarvis preview metadata:

```json
{
  "cloud_forge_context": {
    "task": {
      "task_id": "req-1",
      "domain": "forge/voss/os_architecture",
      "pattern_class": "docs_explanation",
      "mutation_scope": "none"
    },
    "actor": {"wL": 120},
    "tenant": {"latency_bias": 0.4},
    "law_envelope": {
      "law_id": "meta.architect.v1",
      "law_version": "2026-05-28",
      "signals": ["read_only", "docs", "governance"]
    }
  }
}
```

Ledger path override: `CLOUD_FORGE_LEDGER_PATH`.

## Next gate

Phase 3: law-scoped L0–L2 caches.
