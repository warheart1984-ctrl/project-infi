# Coding Policy Pack

Two policy packs ship with `@aaes-os/governed-runtime`:

| Pack | File | Use when |
|------|------|----------|
| **Free** (default for `createFreeCodingAssistant`) | `coding-free.yaml` | Local agents only — no API keys |
| **Full** | `coding.yaml` | Cloud + local (Groq, Codex, etc.) |

## Free Policy Pack (`coding-free.yaml`)

Used automatically by `createFreeCodingAssistant()`:

| Policy ID | When | Route To |
|-----------|------|----------|
| `coding.free.general` | domain=coding, risk=low | Prefer Ollama → LM Studio |
| `coding.free.multi_file` | tags include multi-file | Ollama, DeepSeek, LM Studio |
| `coding.free.local_project` | tags include local-project | Cursor, Ollama, LM Studio |
| `coding.free.agentic` | tags include agentic + tool-use | Devin, Ollama, Cursor |
| `coding.free.sensitive` | tags include sensitive/phi/proprietary | Ollama, LM Studio, local-llm |
| `coding.free.high_risk` | risk=high | Ollama, LM Studio, DeepSeek |

```ts
import { loadFreeCodingPolicyPack } from '@aaes-os/governed-runtime';
const policies = loadFreeCodingPolicyPack();
```

## Full Policy Pack (`coding.yaml`)

| Policy ID | When | Route To |
|-----------|------|----------|
| `coding.general.prefers_groq` | domain=coding, risk=low | Prefer Groq |
| `coding.deepseek.multi_file` | tags include multi-file | DeepSeek-Coder only |
| `coding.cursor.local_project` | tags include local-project | Cursor only |
| `coding.devin.agentic` | tags include agentic + tool-use | Devin only |
| `coding.sensitive.must_use_local` | tags include sensitive/phi/proprietary | Local LLM only |
| `coding.high_risk.prefers_codex` | risk=high | Prefer Codex |

## Loading

```ts
import { loadCodingPolicyPack } from '@aaes-os/governed-runtime';

const policies = loadCodingPolicyPack();
const router = new CodingRouter(backends, policies, ledger);
```

## Custom Policies

Load from custom YAML:

```ts
import { loadPoliciesFromYaml } from '@aaes-os/governed-runtime';
import { readFileSync } from 'node:fs';

const custom = loadPoliciesFromYaml(readFileSync('./my-policies.yaml', 'utf8'));
```
