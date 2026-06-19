#!/usr/bin/env bash
set -euo pipefail
BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()    { echo -e "${BLUE}[linux]${NC} $*"; }
success(){ echo -e "${GREEN}✔${NC} $*"; }
warn()   { echo -e "${YELLOW}⚠${NC}  $*"; }

if command -v apt-get &>/dev/null; then PKG="apt"
elif command -v dnf &>/dev/null; then PKG="dnf"
elif command -v apk &>/dev/null; then PKG="apk"
else echo "Unsupported distro" >&2; exit 1; fi

install() {
  case "$PKG" in
    apt) sudo apt-get install -y -qq "$1" ;;
    dnf) sudo dnf install -y -q "$1" ;;
    apk) sudo apk add -q "$1" ;;
  esac
}

case "$PKG" in
  apt) sudo apt-get update -qq ;;
  dnf) sudo dnf check-update -q || true ;;
  apk) sudo apk update -q ;;
esac

for pkg in git curl wget jq zsh unzip build-essential shellcheck ripgrep fzf; do
  install "$pkg" 2>/dev/null || warn "Could not install $pkg"
done

if ! command -v gh &>/dev/null; then
  if [[ "$PKG" == "apt" ]]; then
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
      https://cli.github.com/packages stable main" \
      | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update -qq && sudo apt-get install -y gh
  fi
fi
success "GitHub CLI ready."

if command -v nvidia-smi &>/dev/null; then
  success "NVIDIA driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
else
  warn "NVIDIA driver NOT found. Install from: https://developer.nvidia.com/cuda-downloads"
fi

[[ ! -d "$HOME/.oh-my-zsh" ]] && RUNZSH=no CHSH=no \
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
P10K="$ZSH_CUSTOM/themes/powerlevel10k"
[[ ! -d "$P10K" ]] && git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$P10K"
for plugin in zsh-autosuggestions zsh-syntax-highlighting; do
  dir="$ZSH_CUSTOM/plugins/$plugin"
  [[ ! -d "$dir" ]] && git clone --depth=1 "https://github.com/zsh-users/$plugin" "$dir"
done

[[ "$SHELL" != "$(command -v zsh)" ]] && sudo chsh -s "$(command -v zsh)" "$USER" 2>/dev/null || true
success "Linux setup complete."
