#!/usr/bin/env bash
# wait-for-service.sh <url> <timeout_seconds>
set -euo pipefail

URL="${1:-}"
TIMEOUT="${2:-60}"

if [ -z "$URL" ]; then
  echo "Usage: $0 <url> [timeout_seconds]"
  exit 2
fi

echo "Waiting for $URL (timeout ${TIMEOUT}s)..."
end=$(( $(date +%s) + TIMEOUT ))
while true; do
  if curl -fsS "$URL" >/dev/null 2>&1; then
    echo "Service $URL is available."
    exit 0
  fi
  now=$(date +%s)
  if [ "$now" -ge "$end" ]; then
    echo "Timed out waiting for $URL"
    exit 1
  fi
  sleep 2
done
