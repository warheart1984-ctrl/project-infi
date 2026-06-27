# SkillzMcGee Lawful Nova Slice Integration

AAES-OS does not require SkillzMcGee to run CTS, CRK-1, or the SDK. This
integration is optional. It is useful when the operator console needs a governed
LLM capability that emits receipts, provenance, continuity events, and law-kernel
verdicts.

## What SkillzMcGee Provides

SkillzMcGee exposes a governed LLM capability named `llm_echo`.

Primary SkillzMcGee user guide:
[docs/USING_SKILLZMCGEE.md](https://github.com/warheart1984-ctrl/skillzmcgee/blob/codex/runtime-integrity-sweep/docs/USING_SKILLZMCGEE.md)

```text
operator request
-> SkillzMcGee runSlice
-> llm_echo capability
-> provider call
-> receipt
-> law kernel verdict
-> continuity events
```

Supported provider modes:

| Mode | Use case | Required service |
|------|----------|------------------|
| Deterministic fallback | Fresh clone, CI, receipt-path smoke test | None |
| Ollama | Local model execution | Ollama on `127.0.0.1:11434` |
| Nova/OpenAI-compatible | Cursor/Nova adapter, secured local gateway, hosted model gateway | `/v1/chat/completions` endpoint |

## Recommended Local Layout

Clone both repos as siblings:

```bash
git clone https://github.com/warheart1984-ctrl/AAES-OS.git
git clone https://github.com/warheart1984-ctrl/skillzmcgee.git
```

Run AAES-OS verification:

```bash
cd AAES-OS
pnpm install
pnpm test:cts
```

Run SkillzMcGee verification:

```bash
cd ../skillzmcgee
npm install
npm test
```

## SkillzMcGee Provider Modes

### Deterministic Fallback

No model or API key is required.

```bash
cd skillzmcgee
npm run nova-studio
```

Run:

```bash
curl -X POST http://127.0.0.1:8787/api/slice/execute \
  -H "Content-Type: application/json" \
  -d '{"sliceId":"llm_echo","payload":{"prompt":"Write a small function."}}'
```

### Ollama

```bash
ollama pull qwen2.5-coder:7b
```

```bash
export NOVA_PROVIDER=ollama
export NOVA_OLLAMA_MODEL=qwen2.5-coder:7b
export NOVA_OLLAMA_BASE_URL=http://127.0.0.1:11434
npm run nova-studio
```

PowerShell:

```powershell
$env:NOVA_PROVIDER = "ollama"
$env:NOVA_OLLAMA_MODEL = "qwen2.5-coder:7b"
$env:NOVA_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
npm run nova-studio
```

### Nova / OpenAI-Compatible Adapter

Use this mode when a local Nova adapter exposes `/v1/chat/completions`.

```bash
export NOVA_PROVIDER=nova
export NOVA_OPENAI_BASE_URL=http://127.0.0.1:18081/v1
export NOVA_OPENAI_MODEL=nova-local
export NOVA_API_KEY=replace-with-your-key
npm run nova-studio
```

PowerShell:

```powershell
$env:NOVA_PROVIDER = "nova"
$env:NOVA_OPENAI_BASE_URL = "http://127.0.0.1:18081/v1"
$env:NOVA_OPENAI_MODEL = "nova-local"
$env:NOVA_API_KEY = "replace-with-your-key"
npm run nova-studio
```

Run:

```bash
curl -X POST http://127.0.0.1:8787/api/slice/execute \
  -H "Content-Type: application/json" \
  -d '{"sliceId":"llm_echo","payload":{"prompt":"Reply with exactly: aaes-ready","model":"nova-local","max_tokens":16}}'
```

Expected receipt output includes:

```json
{
  "provider": "openai-compatible",
  "model": "nova-local",
  "text": "aaes-ready"
}
```

## Cursor And Public HTTPS

Cursor's native model provider may reject private network URLs. If so, expose the
Nova adapter with a static HTTPS tunnel and keep bearer auth enabled.

Cursor settings:

```text
Base URL: https://your-static-tunnel.example/v1
Model: nova-local
API key: your Nova adapter key
```

The AAES-OS side remains unchanged. SkillzMcGee is the governed execution center
for `llm_echo`; AAES-OS consumes its outputs as governed runtime evidence.

## Verification

SkillzMcGee focused check:

```bash
node --test --test-name-pattern "lawful llm slice" tests/nova_studio.test.js
```

SkillzMcGee full Nova Studio surface:

```bash
npm run test:nova-studio
```

AAES-OS conformance:

```bash
pnpm test:cts
```
