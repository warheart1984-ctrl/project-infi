#!/usr/bin/env bash
# Run CORI CI stack + HTTP cross-container proof via WSL Docker.
# Usage (from Windows PowerShell):
#   wsl -d Debian bash /mnt/e/project-infi/scripts/wsl_ci_http_proof.sh
#
# Set WSL_DISTRO=Debian (or your distro) if not using Debian.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p data
chmod +x scripts/wait-for-service.sh scripts/ci_http_stack_proof.sh scripts/ensure_dev_env.sh scripts/docker_compose.sh scripts/wsl_install_buildx.sh
COMPOSE="./scripts/docker_compose.sh"
COMPOSE_FILES="-f docker-compose.ci.yml -f docker-compose.ci-wsl.yml"

echo "=== Docker buildx (compose v5) ==="
./scripts/wsl_install_buildx.sh

echo "=== Python / cori CLI ==="
export PATH="${HOME}/.local/bin:${PATH}"
./scripts/ensure_dev_env.sh
# shellcheck source=/dev/null
if [ -f "$HOME/.venvs/project-infi/bin/activate" ]; then
  . "$HOME/.venvs/project-infi/bin/activate"
elif [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
fi
export PATH="${HOME}/.local/bin:${PATH}"

echo "=== Starting CORI CI stack (in-process AAIS for seed) ==="
# Parallel builds often hit PyPI broken-pipe errors on WSL; build images sequentially.
for svc in lawful_nova aais aaes nexus_dashboard dashboard; do
  img="project-infi-${svc}"
  if docker image inspect "${img}:latest" >/dev/null 2>&1; then
    echo "Skipping $svc (image exists)"
  else
    echo "Building $svc..."
    $COMPOSE $COMPOSE_FILES build "$svc"
  fi
done
$COMPOSE $COMPOSE_FILES up -d

./scripts/wait-for-service.sh http://127.0.0.1:8000/health 180
./scripts/wait-for-service.sh http://127.0.0.1:8080/health 120
./scripts/wait-for-service.sh http://127.0.0.1:8101/health 120
./scripts/wait-for-service.sh http://127.0.0.1:4000/health 120

echo "=== Seed governed mission ==="
if command -v cori >/dev/null 2>&1; then
  AAIS_BASE_URL=http://127.0.0.1:8000 cori mission "wsl local seed" || true
else
  echo "(skip cori CLI — run seed from host venv if needed)"
fi

echo "=== HTTP cross-container proof ==="
./scripts/ci_http_stack_proof.sh

echo ""
echo "=== PASS: HTTP stack proof complete ==="
echo "To tear down: ./scripts/docker_compose.sh $COMPOSE_FILES down -v"
