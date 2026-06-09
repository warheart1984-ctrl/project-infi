#!/bin/bash
# Start AAIS spine / health endpoint (image uses /opt/cogos/bin/start-aais).
set -euo pipefail

START=/opt/cogos/bin/start-aais
if [[ -x "$START" ]]; then
  exec "$START"
fi

# Dev/minimal fallback when payload not staged.
mkdir -p /run/cog
echo '{"status":"ok","mode":"stub"}' >/run/cog/aais.health
if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' &
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/health"):
            body = json.dumps({"status": "ok", "mode": "stub"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *args):
        pass

HTTPServer(("0.0.0.0", 8765), H).serve_forever()
PY
fi
wait
