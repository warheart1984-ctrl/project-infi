# AAIS + AAES-OS + CAB Integration Proof

Date: 2026-06-19
Branch: codex/aaes-os-production-sweep
Workspace: E:\project-infi

## Scope

This proof bundle covers the additive CAB continuity pillar, the AAIS bridge into
AAES-OS ops-console telemetry, and the live governed-runtime receipt path.

CAB remains layered above CCS, Proof, and CVR. It does not replace those systems.

## Implemented Surface

- CAB lineage ledger and invariant evaluator are present under `src/continuity`.
- Nova CVR recompute supports `CAB_AUTO_INGEST=1` and `CAB_STORE`.
- CAB schema and demo lineage fixture are present.
- AAES-OS ops-console exposes CAB state in `/telemetry`.
- AAES-OS ops-console connects to AAIS through `AAIS_BASE_URL`.
- AAES-OS ops-console exposes `/aais/health`.
- AAES-OS UI surfaces AAIS Runtime and CAB Continuity panels.

## Test Evidence

### Continuity and Governance Regression

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cab_blueprint.py tests/test_continuity_reputation_v1.py tests/test_continuity_governance_schema.py tests/test_lawful_nova_lsg.py tests/test_cc01_controlled_collapse_harness.py -q
```

Result:

```text
56 passed in 28.75s
```

### AAES-OS Ops-Console Tests

Command, from `E:\project-infi\aaes-os`:

```powershell
npm run test --workspace @aaes-os/ops-console -- --run src/server.test.ts src/App.test.tsx
```

Result:

```text
Test Files 2 passed (2)
Tests 12 passed (12)
```

### AAES-OS Ops-Console Production Build

Command, from `E:\project-infi\aaes-os`:

```powershell
npm run build --workspace @aaes-os/ops-console
```

Result:

```text
tsc -p tsconfig.json --noEmit && vite build
vite built dist/client successfully
```

### Schema Parse

Command:

```powershell
.\.venv\Scripts\python.exe -c "import json, pathlib; files=['schemas/cab.v1.json','schemas/continuity_governance.v1.json','schemas/ccs_core_objects.v1.json']; [json.loads(pathlib.Path(f).read_text(encoding='utf-8')) for f in files]; print('schema-json-ok:', len(files))"
```

Result:

```text
schema-json-ok: 3
```

## Live Runtime Evidence

### AAIS Health

Endpoint:

```text
http://127.0.0.1:8000/health
```

Observed:

```json
{
  "status": "healthy",
  "service": "AAIS",
  "active_model_mode": "mock",
  "ai_status": "initialized",
  "ai_bootstrap_status": "initialized",
  "mock_mode_active": true,
  "legacy_api_loaded": true
}
```

### AAES-OS Health

Endpoint:

```text
http://127.0.0.1:4000/health
```

Observed:

```json
{
  "ok": true
}
```

### AAES-OS Telemetry

Endpoint:

```text
http://127.0.0.1:4000/telemetry
```

Observed summary:

```json
{
  "aaisConnected": true,
  "aaisStatus": "healthy",
  "aaisMode": "mock",
  "cabAvailable": true,
  "cabInvariantPassed": true,
  "cabEntries": 2,
  "latestReceipt": "cab.receipt.nova-turn-6e085c9e279efdf2,cab.receipt.nova-turn-28e52f985cd2d766"
}
```

### Governed Nova Receipt

Command:

```powershell
$env:CAB_AUTO_INGEST='1'
$env:CAB_STORE=((Resolve-Path .runtime\online).Path + '\cab-ledger.jsonl')
$env:LAWFUL_NOVA_REPO_ROOT=(Resolve-Path .).Path
$env:NOVA_LSG_STORE=((Resolve-Path .runtime\online).Path + '\lsg-store.jsonl')
$env:NOVA_LSG_PATH=(Resolve-Path lsg\LSG-CORE.v1.yaml).Path
.\.venv\Scripts\python.exe -m nova run "observe with continuity - proof push check" --tenant local --capability observe --json
```

Result:

```json
{
  "decision": "EXECUTED",
  "receipt_verified": true,
  "text": "Under RSL, Nova Cortex reads with continuity - proof push check: lawful nova observe health under RSL."
}
```

## Conclusion

The CAB lineage layer, AAIS bridge, AAES-OS telemetry surface, governed Nova
receipt path, and continuity regression suite all passed on 2026-06-19.

The system is proven operational for this integration scope.
