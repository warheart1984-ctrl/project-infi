# AAIS Coding Assistant for VS Code

Governance-first coding assistant powered by AAES-OS AAIS.

## Features

- **Multi-backend routing**: Ollama (local), Groq, OpenRouter (cloud), LM Studio, Cursor, Devin
- **Governance mode**: AAIS flow (llm → jarvis → nova) with constitutional invariants and policy routing
- **General-purpose mode**: Toggle governance off for zero-config general coding
- **Zero-config**: Auto-detects Ollama, reads `GROQ_API_KEY` / `OPENROUTER_API_KEY` from env
- **Preferred backend**: Select which backend to use per session
- **Streaming responses**: Assistant output streams as it's generated
- **Conversation history**: Full chat history within the sidebar panel

## Usage

1. Open the AAIS sidebar panel (click the AAIS icon in the activity bar)
2. Type a prompt and press Enter
3. Use the backend selector to choose Ollama, Groq, or OpenRouter
4. Toggle Governance mode on/off as needed

### Keyboard Shortcut

- `Ctrl+Alt+A` (Win/Linux) / `Cmd+Alt+A` (Mac) — Open AAIS Chat

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `aais.governanceMode` | `true` | Enable governance mode |
| `aais.preferredBackend` | `auto` | Preferred backend (auto, ollama, groq, openrouter-free, lm-studio, cursor) |
| `aais.ollamaUrl` | `http://127.0.0.1:11434` | Ollama server URL |
| `aais.autoDetect` | `true` | Auto-detect available backends |

### API Keys

Set environment variables for cloud backends:

```bash
# Groq (free tier)
setx GROQ_API_KEY "gsk_..."

# OpenRouter (free models available)
setx OPENROUTER_API_KEY "sk-or-..."
```

## Installation

1. Open VS Code
2. Run `Extensions: Install from VSIX...`
3. Select `aais-vscode.vsix`

## Requirements

- VS Code 1.90+
- Node.js 20+ (for Ollama cold-start warmup)
- Ollama installed (optional, for local models)

## License

MIT