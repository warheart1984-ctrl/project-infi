#!/usr/bin/env bash
# Optional CI: bring up dual AAIS mesh peers and probe health endpoints.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/deploy/mesh/docker-compose.federation-ci.yml"
OUT="${COG_MESH_CI_OUT:-$REPO_ROOT/ci-artifacts/mesh-federation-ci.json}"

log() { echo "[mesh-federation-ci] $*" >&2; }

if ! command -v docker >/dev/null 2>&1; then
  echo "mesh-federation-ci: docker not available" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "mesh-federation-ci: docker compose plugin required" >&2
  exit 1
fi

cd "$REPO_ROOT"
log "starting federation-ci stack"
docker compose -f "$COMPOSE_FILE" up -d --build --wait

probe() {
  local url="$1"
  python3 - "$url" <<'PY'
import json, sys, urllib.request
url = sys.argv[1]
with urllib.request.urlopen(url, timeout=10) as resp:
    body = resp.read().decode("utf-8", errors="replace")
print(body)
PY
}

a_health="$(probe "http://127.0.0.1:5000/api/mesh/health")"
b_health="$(docker compose -f "$COMPOSE_FILE" exec -T aais-mesh-b \
  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5001/api/mesh/health').read().decode())")"

mkdir -p "$(dirname "$OUT")"
python3 - "$OUT" "$a_health" "$b_health" <<'PY'
import json, sys
from datetime import datetime, timezone

out, a_raw, b_raw = sys.argv[1:4]
doc = {
    "schema_version": "cog-mesh-federation-ci.v1",
    "status": "pass",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "peers": {"aais-mesh-a": a_raw.strip(), "aais-mesh-b": b_raw.strip()},
}
open(out, "w", encoding="utf-8").write(json.dumps(doc, indent=2) + "\n")
print(out)
PY

log "PASS -> $OUT"
docker compose -f "$COMPOSE_FILE" down -v
