#!/usr/bin/env bash
# Fedora/RHEL dnfroot backend (contract stub).
set -euo pipefail

backend_bootstrap() {
  echo "ERROR: rootfs backend dnfroot is registered but not implemented yet." >&2
  echo "       Contract: docs/forge-rootfs-backend-contract.md" >&2
  echo "       Track: docs/forge-platform-program.md P6" >&2
  exit 4
}
