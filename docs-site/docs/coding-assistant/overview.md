# Coding Assistant Overview

The `@aaes-os/coding-assistant` package is the unified entry point for governed coding workflows.
Every surface now routes through AAIS first in the shared `llm -> jarvis -> nova` order.

## Components

| Module | Package | Purpose |
|--------|---------|---------|
| CodingRouter | `governed-runtime` | Policy-driven backend routing |
| Nova Shell | `nova-shell` | Interactive coding terminal |
| Infinity Agent | `infinity-agents` | Multi-step planner |
| Sandbox | `sandbox` | Safe code execution |

## Free Mode — Use Any Agent for $0

```ts
import { createFreeCodingAssistant } from '@aaes-os/coding-assistant';

const { assistant, aais, discovery } = await createFreeCodingAssistant();
const result = await assistant
  .nova({ actorId: 'jon', role: 'developer' })
  .runCommand('Write a sort function');

console.log(aais.describeFlow());
```

Auto-discovers: **Ollama**, **LM Studio**, **Cursor**, **Devin**, **local LLMs**.

CLI: `pnpm free-coding "your prompt"`

## Full Example (manual setup)

```ts
import { PatternLedger } from '@aaes-os/aaes-governance';
import { CodingAssistant } from '@aaes-os/coding-assistant';
import {
  CodingRouter,
  OllamaBackend,
  loadFreeCodingPolicyPack,
} from '@aaes-os/governed-runtime';

const router = new CodingRouter(
  [new OllamaBackend({ model: 'qwen2.5-coder:3b' })],
  loadFreeCodingPolicyPack(),
  new PatternLedger(),
);

const assistant = new CodingAssistant(router);
const result = await assistant
  .nova({ actorId: 'jon', role: 'developer' })
  .runCommand('Write a Python function to sort a list');

console.log(result.output.text);
```

See also: [Nova Shell](./nova-shell.md), [Infinity Agent](./infinity-agent.md), [Sandbox](./sandbox.md).
