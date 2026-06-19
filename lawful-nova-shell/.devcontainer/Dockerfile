# NVIDIA CUDA 12 base — for Nova Cortex GPU acceleration
FROM nvidia/cuda:12.3.1-cudnn9-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget jq zsh unzip build-essential shellcheck \
    ripgrep fzf bat ca-certificates gnupg && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
      https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list && \
    apt-get update && apt-get install -y gh && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/zsh vscode
USER vscode
WORKDIR /home/vscode

ENV NVM_DIR=/home/vscode/.nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && \
    . "$NVM_DIR/nvm.sh" && nvm install 20 && nvm alias default 20

ENV PYENV_ROOT=/home/vscode/.pyenv
ENV PATH="$PYENV_ROOT/bin:$PATH"
RUN curl https://pyenv.run | bash && \
    eval "$(pyenv init -)" && pyenv install 3.12.4 && pyenv global 3.12.4

RUN RUNZSH=no CHSH=no sh -c \
    "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
RUN ZSH_CUSTOM="/home/vscode/.oh-my-zsh/custom" && \
    git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$ZSH_CUSTOM/themes/powerlevel10k" && \
    git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions" && \
    git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"

RUN mkdir -p /opt/nova/voss-runtime /opt/nova/cortex /opt/nova/gow /opt/nova/rsl /home/vscode/.nova

ENV SHELL=/bin/zsh
ENV CUDA_VISIBLE_DEVICES=0
