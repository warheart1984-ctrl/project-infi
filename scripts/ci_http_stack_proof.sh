#!/usr/bin/env bash
# Cross-container HTTP proof: Nova → UGR → AAIS → AAES → Nexus (live docker stack).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/wait-for-service.sh scripts/docker_compose.sh
COMPOSE="./scripts/docker_compose.sh"
COMPOSE_FILES=(-f docker-compose.ci.yml)
if [ -n "${CORI_COMPOSE_WSL:-}" ] || [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; then
  COMPOSE_FILES+=(-f docker-compose.ci-wsl.yml)
fi
COMPOSE_FILES+=(-f docker-compose.ci-http.yml)

if ! command -v cori >/dev/null 2>&1; then
  if [ -f "$HOME/.venvs/project-infi/bin/activate" ]; then
    # shellcheck source=/dev/null
    . "$HOME/.venvs/project-infi/bin/activate"
  elif [ -f "$ROOT/.venv/bin/activate" ]; then
    # shellcheck source=/dev/null
    . "$ROOT/.venv/bin/activate"
  fi
fi

echo "=== Recreating AAIS in HTTP mode (no in-process stubs) ==="
$COMPOSE "${COMPOSE_FILES[@]}" up -d --no-deps --force-recreate aais

echo "=== Waiting for services ==="
./scripts/wait-for-service.sh http://127.0.0.1:8080/health 120
./scripts/wait-for-service.sh http://127.0.0.1:8000/health 120
./scripts/wait-for-service.sh http://127.0.0.1:8101/health 90
./scripts/wait-for-service.sh http://127.0.0.1:4000/health 90

echo "=== HTTP governed mission (cori CLI) ==="
AAIS_BASE_URL=http://127.0.0.1:8000 cori mission "ci http cross-container proof" --json | tee http_mission.out

echo "=== Full stack proof (HTTP mode) ==="
FULL_STACK_PROOF_MODE=http python scripts/full_system_proof.py --json --out http_stack_proof.json
cat http_stack_proof.json

echo "=== Nexus ledger cross-port check ==="
curl -fsS http://127.0.0.1:8000/api/nexus/executions | tee nexus_aais.json
curl -fsS http://127.0.0.1:4000/api/nexus/executions | tee nexus_ops.json

echo "=== HTTP stack proof complete ==="
