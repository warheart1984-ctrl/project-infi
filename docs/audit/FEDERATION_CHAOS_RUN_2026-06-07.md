# Federation Chaos Run — 2026-06-07

Target: `http://127.0.0.1:8000` (live AAIS, health 200 pre/post)

## Verdict

| Phase | Probes | Result |
|-------|--------|--------|
| A — Civilizational surface farm | 8 | **PASS** (all GET 200) |
| B — Civilizational governance abuse | 72 | **PASS** (403/400/405 as expected, 0×5xx) |
| B2 — Concurrent observe burst | 32 | **PASS** (0×5xx) |
| C — UGR cross-tenant federation | 10 | **PASS** (400/403/422 as expected, 0×5xx) |
| **Total** | **92** | **PASS** |

**Health:** preflight 200, postflight 200. **0×5xx**, **0 unexpected failures**.

Federation-grade tier exercises dual-gate `observe`/`adopt` paths on civilizational-arc operator routes and UGR federated mission + ODL graph abuse — above generic chaos hammer (which only GET-probes operator console/ledger).

## Phase detail

### A — Civilizational GET surfaces

- `/api/operator/norm-federations`, `.../treaties`
- `/api/operator/diplomacy`, `.../accords`
- `/api/operator/constitutional-evolution`, `.../amendments`
- `/api/operator/civilizations`, `.../charters`

### B — Governance abuse (per subsystem)

For norm federation, diplomacy, constitutional evolution, governed civilization:

- **Observe:** empty body, negative/huge `window_days`, path-traversal `session_id`, 50k-char overflow
- **Adopt:** missing approval, approved-without-candidate, injected candidate, `operator_approved: false`, GET on adopt endpoint

### C — UGR federation

- Federated mission abuse via `POST /api/ugr/mission/run` (missing grant, bogus grant, tenant traversal, smoke grant wrong tenant, overflow step)
- ODL graph abuse via `GET /api/operator/ledger/federation/<grant_id>/graph` (smoke-grant, traversal, SQL injection, 500-char id, null byte)

## Artifacts

- `ci-artifacts/federation_chaos_report.json`
- `ci-artifacts/federation_chaos_postfix_2026-06-07.txt`

## Reproduction

```powershell
cd e:\project-infi
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
python tools/stress/federation_chaos_hammer.py
make federation-chaos-gate
python -m pytest tests/test_federation_chaos_hammer.py -q
```

Full stress stack (generic + federation + seam):

```powershell
make flagship-chaos-stack
```

## Related

- Generic hammer: `docs/audit/FLAGSHIP_CHAOS_HAMMER_2026-06-07.md`
- Seam discovery: `docs/audit/SEAM_STRESS_RUN_2026-06-07.md`

## Out of scope

- Successful live treaty adoption (would pollute mock runtime)
- 6 `workflow_family_*` genome route gaps
- Distributed multi-instance mesh (`scenario_federation_dual_ledger` stays unit/offline)
