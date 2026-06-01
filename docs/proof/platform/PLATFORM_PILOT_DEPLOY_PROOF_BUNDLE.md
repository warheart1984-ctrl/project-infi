# Platform Pilot Deploy Proof Bundle

**Claim:** Infinity Pilot full-stack compose path (Platform + Postgres + Redis + MinIO + AAIS) — **asserted** local; **proven** when operator captures compose smoke log below on target environment.

## Verification

```bash
make platform-v6-gate
make platform-v6-smoke
python scripts/pilot_compose_smoke.py --local
```

## Compose bootstrap

```bash
cd deploy/pilot
cp .env.example .env
docker compose up --build -d
python ../../scripts/pilot_compose_smoke.py --base-url http://127.0.0.1:8090 --api-key change-me-pilot-master
```

## Evidence checklist

| Step | Expected | Claim |
|------|----------|-------|
| `GET /v1/health` | 200 | asserted |
| Create org + job | 200 | asserted |
| `GET .../ledger/verify` | valid=true | asserted |
| Sovereign export pack | application/zip | asserted |
| Cross-machine tertiary CI | green | proven — record URL in PLATFORM_V43_V44 bundle |

## CI cross-machine (PLAT-D31)

Workflow: `.github/workflows/platform-cross-machine-gate.yml`

**Operator:** paste green tertiary run URL:

```
CI_RUN_URL=(fill after push)
```
