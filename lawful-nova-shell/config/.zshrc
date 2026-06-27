# ── Lawful Nova Agentic Shell (zsh) ───────────────────────────────────────────
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting fzf gh docker node python)
[[ -f "$ZSH/oh-my-zsh.sh" ]] && source "$ZSH/oh-my-zsh.sh"
[[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh

[[ -f "$HOME/.novarc" ]] && source "$HOME/.novarc"

export LAWFUL_NOVA_REPO_ROOT="${LAWFUL_NOVA_REPO_ROOT:-$HOME/agentic-coding-agent}"
[[ -d "$LAWFUL_NOVA_REPO_ROOT/bin" ]] && export PATH="$LAWFUL_NOVA_REPO_ROOT/bin:$PATH"
[[ -n "${NOVA_VOSS_RUNTIME_PATH:-}" ]] && export PATH="$NOVA_VOSS_RUNTIME_PATH:$PATH"
[[ -n "${NOVA_RSL_PATH:-}" ]]          && export PATH="$NOVA_RSL_PATH:$PATH"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)" 2>/dev/null || true

export PATH="$HOME/.local/bin:$HOME/bin:/usr/local/bin:$PATH"
export EDITOR="${EDITOR:-code --wait}"

HISTSIZE=50000; SAVEHIST=50000; HISTFILE="$HOME/.zsh_history"
setopt HIST_IGNORE_DUPS HIST_IGNORE_SPACE SHARE_HISTORY AUTO_CD

alias ..='cd ..'; alias ...='cd ../..'
alias ll='eza -la --git --icons 2>/dev/null || ls -la'
alias cat='bat --style=plain 2>/dev/null || cat'
alias gs='git status'; alias ga='git add'; alias gc='git commit'; alias gp='git push'
alias gl='git pull'; alias gd='git diff'; alias glog='git log --oneline --graph --decorate --all'

NOVA="${NOVA_CLI:-$LAWFUL_NOVA_REPO_ROOT/bin/nova}"
alias nova-chat="$NOVA chat"

novr() {
  echo "🌌 Nova reviewing staged changes..."
  git status && git diff --cached
  $NOVA run "Review these staged git changes. Identify any issues. Then write a conventional commit message and commit."
}

novtest() {
  echo "🌌 Nova running test suite..."
  $NOVA run "Run all tests in this project. If any fail, identify the root cause and fix the source code. Re-run until all pass. Max 5 iterations."
}

novpr() {
  echo "🌌 Nova creating PR..."
  $NOVA run "Compare this branch to main. Generate a conventional PR title and a detailed description (What, Why, How to test). Then run: gh pr create --title '<title>' --body '<body>'"
}

novdoc() {
  echo "🌌 Nova generating documentation..."
  $NOVA run "Analyze all source files in the current directory. Generate comprehensive documentation and write it to README.md."
}

novsec() {
  echo "🌌 Nova running security audit..."
  $NOVA run "Perform a thorough security audit of this codebase. Check for: hardcoded secrets, injection vulnerabilities, insecure dependencies, missing auth checks. Output a severity-ranked report."
}

novrefactor() {
  [[ -z "${1:-}" ]] && echo "Usage: novrefactor <file>" && return 1
  echo "🌌 Nova refactoring $1..."
  $NOVA run "Refactor $1 for improved readability, maintainability, and performance. Preserve all existing behavior and public API. Run tests after."
}

novstack() {
  echo "🌌 Nova Stack Status"
  echo "  API:     ${NOVA_API_URL:-not set}"
  echo "  GPU:     $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo 'N/A')"
  echo "  Cortex:  ${NOVA_CORTEX_PATH:-not set}"
  echo "  Voss:    ${NOVA_VOSS_RUNTIME_PATH:-not set}"
  echo "  GoW cfg: ${NOVA_GOW_CONFIG:-not set}"
  curl -sf "${NOVA_API_URL:-http://localhost:8080}/health" &>/dev/null \
    && echo "  Health:  ✔ API responding" \
    || echo "  Health:  ✖ API not responding"
}

export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border"
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --glob "!.git"'

autoload -Uz compinit && compinit

echo ""
echo "🌌 Lawful Nova shell ready (zsh)."
echo "   nova chat | novr | novtest | novpr | novdoc | novsec | novstack"
echo ""
