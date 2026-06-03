# Frontier model adapters

AAIS registers frontier providers in the Jarvis provider registry. Adapters are **listed for every user**; they turn **on** only when the matching API key (and endpoint, if required) is set in `.env`.

## Built-in providers

| ID | Display name | Activation |
| --- | --- | --- |
| `local` | Local Heroine | Always on (on-laptop model or mock) |
| `claude` | Claude — First Sister | `ANTHROPIC_API_KEY` |
| `openrouter` | OpenRouter — Free Relay | `OPENROUTER_API_KEY` |

## Frontier catalog (HTTP / OpenAI-compatible)

| ID | Family | Default model | Key env |
| --- | --- | --- | --- |
| `openai` | OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` |
| `google` | Gemini | `gemini-2.0-flash` | `GOOGLE_API_KEY` / `GEMINI_API_KEY` |
| `mistral` | Mistral | `mistral-large-latest` | `MISTRAL_API_KEY` |
| `deepseek` | DeepSeek | `deepseek-chat` | `DEEPSEEK_API_KEY` |
| `xai` | Grok | `grok-2-latest` | `XAI_API_KEY` |
| `groq` | Groq | `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| `together` | Together | Llama 3.1 70B Turbo | `TOGETHER_API_KEY` |
| `fireworks` | Fireworks | Llama 3.1 70B | `FIREWORKS_API_KEY` |
| `perplexity` | Sonar | `sonar` | `PERPLEXITY_API_KEY` |
| `nvidia` | **Nemotron 3** | `nvidia/nemotron-3-nano-30b-a3b` | `NVIDIA_API_KEY` |
| `azure_openai` | Azure GPT | deployment name | `AZURE_OPENAI_API_KEY` + endpoint |
| `moonshot` | Kimi | `moonshot-v1-8k` | `MOONSHOT_API_KEY` |
| `ai21` | Jamba | `jamba-large` | `AI21_API_KEY` |

Aliases (e.g. `gemini` → `google`, `nemotron` → `nvidia`) are accepted in session `preferred_provider`.

## NVIDIA Nemotron (new)

NVIDIA’s current open frontier line is **Nemotron 3** (Nano available; Super/Ultra expected H1 2026). The **Nemotron Coalition** is co-developing the base for **Nemotron 4**.

- **Hosted:** `integrate.api.nvidia.com` with `NVIDIA_API_KEY` from [build.nvidia.com](https://build.nvidia.com)
- **Self-hosted NIM:** set `AAIS_NVIDIA_BASE_URL` to your NIM host (e.g. `http://127.0.0.1:8000/v1/chat/completions`)
- **Reasoning traces:** `AAIS_NVIDIA_ENABLE_THINKING=1` passes `chat_template_kwargs.enable_thinking` to the API

## API

- List providers: `GET /legacy_api/api/jarvis/providers`
- Pick provider on chat/session: `preferred_provider` (e.g. `"nvidia"`, `"openai"`)

## Code layout

- `src/providers/frontier_catalog.py` — specs and defaults
- `src/providers/http_chat_provider.py` — shared OpenAI-compatible adapter
- `src/providers/registry_bootstrap.py` — registers catalog on `provider_registry.refresh()`
