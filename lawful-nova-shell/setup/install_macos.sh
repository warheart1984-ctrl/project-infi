#!/usr/bin/env bash
set -euo pipefail
BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()    { echo -e "${BLUE}[macos]${NC} $*"; }
success(){ echo -e "${GREEN}✔${NC} $*"; }
warn()   { echo -e "${YELLOW}⚠${NC}  $*"; }

if ! xcode-select -p &>/dev/null; then
  xcode-select --install
  until xcode-select -p &>/dev/null; do sleep 5; done
fi
success "Xcode CLT ready."

if ! command -v brew &>/dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  [[ "$(uname -m)" == "arm64" ]] && eval "$(/opt/homebrew/bin/brew shellenv)" && \
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
fi
brew update --quiet
success "Homebrew ready."

for pkg in git curl wget jq ripgrep fzf fd gh zsh bat eza shellcheck; do
  brew list "$pkg" &>/dev/null || brew install "$pkg" --quiet
  success "$pkg"
done

[[ ! -d "$HOME/.oh-my-zsh" ]] && RUNZSH=no CHSH=no \
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
P10K="$ZSH_CUSTOM/themes/powerlevel10k"
[[ ! -d "$P10K" ]] && git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$P10K"
for plugin in zsh-autosuggestions zsh-syntax-highlighting; do
  dir="$ZSH_CUSTOM/plugins/$plugin"
  [[ ! -d "$dir" ]] && git clone --depth=1 "https://github.com/zsh-users/$plugin" "$dir"
  success "Plugin: $plugin"
done

warn "NVIDIA GPU acceleration requires Linux. On Apple Silicon, Nova Cortex may use MPS (Metal)."
warn "Set NOVA_GPU_DEVICE=mps in ~/.novarc if using Apple Silicon."

command -v code &>/dev/null || brew install --cask visual-studio-code --quiet 2>/dev/null || true
success "macOS setup complete."
