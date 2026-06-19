#!/usr/bin/env bash
# install_nova.sh — Validates and wires the Nova LLM stack
set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()    { echo -e "${BLUE}[nova]${NC} $*"; }
success(){ echo -e "${GREEN}✔${NC} $*"; }
warn()   { echo -e "${YELLOW}⚠${NC}  $*"; }

[[ -f "$HOME/.novarc" ]] && source "$HOME/.novarc"

NOVA_PORT="${NOVA_PORT:-8080}"
NOVA_CLI="${NOVA_CLI:-nova}"
NOVA_VOSS_RUNTIME_PATH="${NOVA_VOSS_RUNTIME_PATH:-}"
NOVA_CORTEX_PATH="${NOVA_CORTEX_PATH:-}"

log "Validating Nova LLM stack..."

if [[ -n "$NOVA_VOSS_RUNTIME_PATH" && -d "$NOVA_VOSS_RUNTIME_PATH" ]]; then
  success "Voss Runtime found: $NOVA_VOSS_RUNTIME_PATH"
  if [[ ":$PATH:" != *":$NOVA_VOSS_RUNTIME_PATH:"* ]]; then
    export PATH="$NOVA_VOSS_RUNTIME_PATH:$PATH"
    grep -q "NOVA_VOSS_RUNTIME_PATH" "$HOME/.novarc" 2>/dev/null || \
      echo "export PATH=\"$NOVA_VOSS_RUNTIME_PATH:\$PATH\"" >> "$HOME/.novarc"
  fi
else
  warn "NOVA_VOSS_RUNTIME_PATH not set or not found."
fi

if [[ -n "$NOVA_CORTEX_PATH" && -d "$NOVA_CORTEX_PATH" ]]; then
  success "Nova Cortex found: $NOVA_CORTEX_PATH"
else
  warn "NOVA_CORTEX_PATH not set or not found."
fi

if command -v "$NOVA_CLI" &>/dev/null; then
  success "Nova CLI reachable: $(command -v "$NOVA_CLI")"
else
  warn "Nova CLI ('$NOVA_CLI') not found in PATH."
fi

NOVA_API_URL="${NOVA_API_URL:-http://localhost:${NOVA_PORT}}"
if curl -sf "${NOVA_API_URL}/health" &>/dev/null; then
  success "Nova API responding at ${NOVA_API_URL}"
else
  warn "Nova API not responding at ${NOVA_API_URL} — is the stack running?"
fi

if command -v nvidia-smi &>/dev/null; then
  GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
  GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)
  success "NVIDIA GPU: $GPU_NAME ($GPU_MEM)"
else
  warn "nvidia-smi not found. GPU acceleration unavailable."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
mkdir -p "$HOME/.nova"
if [[ -f "$REPO_ROOT/config/nova/nova-stack.json" ]]; then
  cp "$REPO_ROOT/config/nova/nova-stack.json" "$HOME/.nova/nova-stack.json"
  success "nova-stack.json deployed to ~/.nova/"
fi

log "Nova stack validation complete."
