#!/usr/bin/env bash
# docker-compose v5+ needs buildx >= 0.17; Debian package is often older.
set -euo pipefail

need_upgrade=false
if ! docker buildx version >/dev/null 2>&1; then
  need_upgrade=true
elif docker buildx version 2>/dev/null | grep -Eq 'v0\.(1[0-6]|[0-9])\.'; then
  need_upgrade=true
fi

if [ "$need_upgrade" != true ]; then
  exit 0
fi

echo "Upgrading docker buildx (compose v5 requires >= 0.17)..."
mkdir -p "${HOME}/.docker/cli-plugins"
arch="$(uname -m)"
case "$arch" in
  x86_64) bx_arch=amd64 ;;
  aarch64|arm64) bx_arch=arm64 ;;
  *) echo "Unsupported arch: $arch" >&2; exit 1 ;;
esac
curl -fsSL -o "${HOME}/.docker/cli-plugins/docker-buildx" \
  "https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-${bx_arch}"
chmod +x "${HOME}/.docker/cli-plugins/docker-buildx"
docker buildx version
