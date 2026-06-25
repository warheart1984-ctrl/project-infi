#!/usr/bin/env bash
# bootstrap.sh — Lawful Nova Agentic Shell Bootstrap (macOS / Linux)
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${BLUE}[nova-bootstrap]${NC} $*"; }
success(){ echo -e "${GREEN}✔${NC} $*"; }
warn()   { echo -e "${YELLOW}⚠${NC}  $*"; }
error()  { echo -e "${RED}✖${NC}  $*" >&2; exit 1; }
banner() { echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════${NC}"; \
           echo -e "${BOLD}${CYAN}  $*${NC}"; \
           echo -e "${BOLD}${CYAN}═══════════════════════════════════════${NC}\n"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
NON_INTERACTIVE=false

usage() {
  cat <<EOF
Usage: setup/bootstrap.sh [--non-interactive]

Options:
  --non-interactive, -y   Use local defaults and skip prompts.
  --help, -h              Show this help.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --non-interactive|-y) NON_INTERACTIVE=true ;;
    --help|-h) usage; exit 0 ;;
    *) error "Unknown option: $arg" ;;
  esac
done

if [[ ! -t 0 ]]; then
  NON_INTERACTIVE=true
fi

prompt_value() {
  local prompt_text="$1" default="$2" val=""
  if [[ "$NON_INTERACTIVE" == true ]]; then
    log "$prompt_text -> $default (default, non-interactive)"
    printf '%s\n' "$default"
    return
  fi
  read -rp "$prompt_text [default: $default]: " val
  printf '%s\n' "${val:-$default}"
}

banner "🌌 Lawful Nova Agentic Shell Bootstrap"
log "Repo root : $REPO_ROOT"
log "Date/Time : $(date)"

OS=""
if [[ "$(uname)" == "Darwin" ]]; then
  OS="macos"; log "Detected: macOS $(sw_vers -productVersion)"
elif [[ "$(uname)" == "Linux" ]]; then
  OS="linux"; log "Detected: Linux"
else
  error "Unsupported OS: $(uname). Use setup/bootstrap.ps1 on Windows."
fi

banner "Step 1/6 — System Dependencies"
if [[ "$OS" == "macos" ]]; then bash "$SCRIPT_DIR/install_macos.sh"
else bash "$SCRIPT_DIR/install_linux.sh"; fi
success "System dependencies ready."

banner "Step 2/6 — Node.js 20 & Python 3.12"
export NVM_DIR="$HOME/.nvm"
[[ ! -d "$NVM_DIR" ]] && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm ls 20 &>/dev/null || nvm install 20
nvm alias default 20 && nvm use default --silent
success "Node.js $(node --version) ready."

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
[[ ! -d "$PYENV_ROOT" ]] && curl https://pyenv.run | bash
eval "$(pyenv init -)" 2>/dev/null || true
pyenv versions | grep -q "3.12" || pyenv install 3.12.4 --skip-existing
pyenv global 3.12.4
success "Python $(python --version) ready."

PYTHON_BIN="$(command -v python3.12 || command -v python3 || command -v python)"
if [[ ! -x "$REPO_ROOT/.venv/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$REPO_ROOT/.venv"
fi
"$REPO_ROOT/.venv/bin/python" -m pip install --upgrade pip
"$REPO_ROOT/.venv/bin/python" -m pip install -e "$REPO_ROOT"
success "Local Lawful Nova package installed in .venv."

banner "Step 3/6 — Nova Stack Validation"
bash "$SCRIPT_DIR/install_nova.sh"
success "Nova stack validated."

banner "Step 4/6 — Linking Config Files"
link_cfg() {
  local src="$1" dst="$2"
  [[ -f "$dst" && ! -L "$dst" ]] && mv "$dst" "${dst}.bak" && warn "Backed up $dst"
  ln -sf "$src" "$dst" && success "Linked: $dst"
}
link_cfg "$REPO_ROOT/config/.zshrc"    "$HOME/.zshrc"
if [[ -f "$HOME/.novarc" && ! -f "$HOME/.novarc.bak" ]]; then
  cp "$HOME/.novarc" "$HOME/.novarc.bak"
  warn "Backed up $HOME/.novarc"
fi
cp "$REPO_ROOT/config/.novarc" "$HOME/.novarc"
success "Deployed: $HOME/.novarc"
mkdir -p "$HOME/.nova"
link_cfg "$REPO_ROOT/config/nova/nova-stack.json" "$HOME/.nova/nova-stack.json"
export LAWFUL_NOVA_REPO_ROOT="$REPO_ROOT"
grep -q 'LAWFUL_NOVA_REPO_ROOT' "$HOME/.novarc" 2>/dev/null || \
  echo "export LAWFUL_NOVA_REPO_ROOT=\"$REPO_ROOT\"" >> "$HOME/.novarc"

if [[ ! -f "$HOME/.gitconfig" ]]; then
  if [[ "$NON_INTERACTIVE" == true ]]; then
    warn "No ~/.gitconfig; skipping git identity (run bootstrap interactively or create manually)."
  else
    read -rp "Git name: " GIT_NAME
    read -rp "Git email: " GIT_EMAIL
    sed -e "s/{{GIT_NAME}}/$GIT_NAME/" \
        -e "s/{{GIT_EMAIL}}/$GIT_EMAIL/" \
        "$REPO_ROOT/config/.gitconfig.template" > "$HOME/.gitconfig"
    success "~/.gitconfig created."
  fi
fi

banner "Step 5/6 — Nova Stack Paths"
NOVARC="$HOME/.novarc"
set_nova_var() {
  local var="$1" prompt_text="$2" default="$3"
  if grep -q "^export ${var}=" "$NOVARC" 2>/dev/null && \
     ! grep -q "^export ${var}=\"\"" "$NOVARC" 2>/dev/null; then
    success "$var already set."
    return
  fi
  VAL="$(prompt_value "$prompt_text" "$default")"
  sed -i.bak "/^export ${var}/d" "$NOVARC" 2>/dev/null || true
  echo "export ${var}=\"${VAL}\"" >> "$NOVARC"
  success "$var set."
}

set_nova_var "NOVA_PORT"              "Nova API port"                 "8080"
set_nova_var "NOVA_CLI"               "Nova CLI command"              "$REPO_ROOT/bin/nova"
set_nova_var "NOVA_VOSS_RUNTIME_PATH" "Path to Voss Runtime"         "$REPO_ROOT/nova"
set_nova_var "NOVA_CORTEX_PATH"       "Path to Nova Cortex"          "$REPO_ROOT/nova"
set_nova_var "NOVA_GOW_CONFIG"        "Path to Gates of Wonder config" "$REPO_ROOT/config/nova/nova-stack.json"
set_nova_var "NOVA_RSL_PATH"          "Path to RSL"                  "$REPO_ROOT/governance"
set_nova_var "NOVA_GPU_DEVICE"        "NVIDIA GPU device index"      "0"
set_nova_var "GITHUB_TOKEN"           "GitHub PAT (optional)"        ""

banner "Step 6/6 — Verification"
bash "$SCRIPT_DIR/verify.sh"

echo ""
echo -e "${BOLD}${GREEN}🌌 Nova shell bootstrap complete!${NC}"
echo ""
echo "  Reload your shell : source ~/.zshrc"
echo "  Start Nova        : nova-chat"
echo "  One-shot prompt   : nova run \"your task here\""
echo "  Diagnostics       : ./setup/verify.sh --verbose"
echo ""
