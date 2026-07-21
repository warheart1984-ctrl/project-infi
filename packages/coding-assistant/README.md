# AAES-OS Coding Assistant

Governed, multi-backend, Codex-style coding engine for stable, accountable development workflows.
All public assistant surfaces now pass through AAIS first using the shared `llm -> jarvis -> nova` order.

## Free mode (no API keys)

Use **any local agent for free** — Ollama, LM Studio, Cursor, Devin, or any OpenAI-compatible local server:

```ts
import { createFreeCodingAssistant } from '@aaes-os/coding-assistant';

const { assistant, aais, discovery } = await createFreeCodingAssistant();

console.log('Available:', discovery.available.map((a) => a.name));
// e.g. ['ollama', 'lm-studio']
console.log('AAIS flow:', aais.describeFlow());
console.log('SovereignX router:', assistant.getSovereignXRouter() ? 'ready' : 'missing');

const result = await assistant
  .nova({ actorId: 'jon', role: 'developer' })
  .runCommand('Write a TypeScript sort function');

console.log(result.output.text);
```

### One-liner CLI

```bash
# Start a free agent first
ollama serve
ollama pull qwen2.5-coder:3b

# Then run
pnpm free-coding "Write a Python function to sort a list"
pnpm free-coding --infinity "Build a CLI todo app in Rust"
```

### Supported free agents

| Agent | Default URL | Env var |
|-------|-------------|---------|
| Ollama | `http://127.0.0.1:11434` | `OLLAMA_HOST`, `OLLAMA_MODEL` |
| LM Studio | `http://127.0.0.1:1234` | `LM_STUDIO_URL`, `LM_STUDIO_MODEL` |
| Cursor (local) | `http://127.0.0.1:5100` | — |
| Devin (local) | `http://127.0.0.1:8000` | — |
| Local LLM | `http://127.0.0.1:8080` | — |

Auto-discovery probes each endpoint at startup. The free policy pack (`coding-free.yaml`) routes tasks to the best available local backend.
When both `qwen2.5-coder:3b` and `qwen2.5-coder:7b` are present in Ollama, the assistant now wraps them in a SovereignX router so small prompts favor the 3B model and larger prompts favor the 7B model.

### Plug in any OpenAI-compatible agent

```ts
import { createFreeCodingAssistant } from '@aaes-os/coding-assistant';
import { OpenAiCompatibleBackend } from '@aaes-os/governed-runtime';

const { assistant } = await createFreeCodingAssistant({
  additionalBackends: [
    new OpenAiCompatibleBackend({
      name: 'my-vllm',
      baseUrl: 'http://192.168.1.50:8000',
      model: 'starcoder2',
    }),
  ],
});
```

---

## Full mode (cloud + local)

The AAES-OS Coding Assistant is a governed, multi-backend coding system that unifies Codex, Cursor, Devin, DeepSeek-Coder, Groq LLaMA-3, local LLMs, and any future coding engines behind a single, policy-driven interface.
It now routes those surfaces through AAIS before Nova, Infinity, or Sandbox construction.

It is part of the AAES-OS governed runtime, providing:

- Policy-driven routing across multiple coding engines
- Full lifecycle traceability via the Pattern Ledger
- Capability-graph-based permissions
- Governed code execution sandbox
- Nova Coding Shell (interactive terminal)
- Infinity Coding Agent (multi-step planner)
- Universal Coding Backend Adapters
- Vendor-agnostic inference layer

This module turns AAES-OS into a Codex-class coding assistant, but governed, auditable, and multi-backend.

## Features

### Multi-Backend Coding Engine

Plug in any coding model or service:

- Codex (OpenAI-compatible)
- Cursor (local API)
- Devin (local agent API)
- DeepSeek-Coder (Ollama / OpenAI-compatible)
- Groq LLaMA-3
- LM Studio / Ollama / local LLMs
- Future backends

All unified behind the `CodingBackend` interface.

### Governed Routing

Policies in `governed-runtime/src/policies/coding.yaml` determine which backend is used:

| Task | Backend |
|------|---------|
| Fast general coding | Groq |
| Multi-file reasoning | DeepSeek-Coder |
| Local project refactoring | Cursor |
| Agentic tool-use | Devin |
| Sensitive code | Local LLM |

### Nova Coding Shell

A Codex-style governed terminal:

```ts
const nova = assistant.nova({ actorId: 'jon', role: 'developer' });
const result = await nova.runCommand('Refactor this function');
```

### Infinity Coding Agent

A multi-step coding planner:

```ts
const infinity = assistant.infinity({ actorId: 'jon', role: 'developer' });
const solution = await infinity.solve('Build a REST API in Node.js');
```

### Governed Code-Execution Sandbox

Safe, isolated code execution:

```ts
const sandbox = assistant.sandbox({ allowedModules: ['path'] });
const output = sandbox.execute("console.log('Hello')");
```

## Installation

Inside the AAES-OS monorepo:

```bash
pnpm install
pnpm --filter @aaes-os/coding-assistant build
```

## Usage

```ts
import { PatternLedger } from '@aaes-os/aaes-governance';
import { CodingAssistant } from '@aaes-os/coding-assistant';
import {
  CodingRouter,
  CodexBackend,
  CursorBackend,
  DeepSeekCoderBackend,
  GroqBackend,
  LocalLlmBackend,
  loadCodingPolicyPack,
} from '@aaes-os/governed-runtime';

const router = new CodingRouter(
  [
    new CodexBackend(process.env.OPENAI_API_KEY!),
    new CursorBackend(),
    new DeepSeekCoderBackend(),
    new GroqBackend(process.env.GROQ_API_KEY!),
    new LocalLlmBackend('http://localhost:8080'),
  ],
  loadCodingPolicyPack(),
  new PatternLedger(),
);

const assistant = new CodingAssistant(router);
```

## Repository Structure

```
packages/
├── governed-runtime/   # CodingRouter, backends, policy pack
├── nova-shell/         # NovaCodingShell
├── infinity-agents/    # InfinityCodingAgent
├── sandbox/            # GovernedSandbox
└── coding-assistant/   # Unified facade (this package)
```

## Testing

```bash
pnpm --filter @aaes-os/coding-assistant test
pnpm --filter @aaes-os/governed-runtime test
```

## Part of AAES-OS

This module integrates with:

- `@aaes-os/governed-runtime`
- `@aaes-os/aaes-governance` (Pattern Ledger)
- `@aaes-os/architect-agent` (single-backend Ollama agent)
- `@aaes-os/ucr-runtime`

## License

MIT
