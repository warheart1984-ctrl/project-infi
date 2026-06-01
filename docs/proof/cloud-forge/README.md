# Cloud Forge proof artifacts

| File | Purpose |
|---|---|
| `C0_PHASE0_PROOF.md` | Governance contract + failsafe |
| `C1_RAIL_SCHEDULER_PROOF.md` | Rail scheduler library |
| `C2_OBSERVATION_PROOF.md` | Ledger + template + Jarvis readout |
| `C3_CACHE_PROOF.md` | Law-scoped L0–L2 caches |
| `C4_LOCALITY_PROOF.md` | Domain slices, priority, prewarm, tempering |
| `rail-decisions.jsonl` | Append-only rail decision log (created at runtime) |

Runtime cache files live under `.runtime/cloud_forge/cache/` (override: `CLOUD_FORGE_CACHE_ROOT`).

Do not hand-edit `rail-decisions.jsonl` for proof claims; use test temp paths or verified append API.
