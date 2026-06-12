#!/bin/bash
# Start USL spine / health endpoint (image uses /opt/cogos/bin/start-usl).
set -euo pipefail

START=/opt/cogos/bin/start-usl
if [[ -x "$START" ]]; then
  exec "$START"
fi

# Dev/minimal fallback when payload not staged.
HEALTH_PORT="${COG_USL_PORT:-8766}"
RUN=/run/cog
mkdir -p "$RUN"
echo '{"status":"degraded","service":"usl","runtime":"missing"}' >"$RUN/usl.health"
python3 - <<PY &
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HEALTH_FILE = Path("${RUN}/usl.health")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/health"):
            body = HEALTH_FILE.read_bytes() if HEALTH_FILE.is_file() else b'{"status":"unknown"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, fmt, *args):
        pass

HTTPServer(("0.0.0.0", int("${HEALTH_PORT}")), HealthHandler).serve_forever()
PY
wait
