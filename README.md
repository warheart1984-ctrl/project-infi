# AAIS — Adaptive Autonomous Intelligence System

A Next.js + TypeScript AI assistant with streaming chat, long-term memory, tool execution, and multi-step planning. Powered by OpenAI.

## Features

- **Streaming chat** — real-time SSE token-by-token responses
- **Long-term memory** — in-memory vector similarity search that remembers past conversations
- **Short-term memory** — sliding window of recent messages with automatic summarization
- **Tool execution** — 8 built-in tools (calculator, datetime, text utils, UUID, base64, JSON formatter, echo, web search stub)
- **Multi-step planner** — automatically breaks complex requests into actionable steps
- **Executor module** — validates and runs tool calls with structured error handling
- **Dark-themed chat UI** — auto-scroll, Enter-to-send, streaming indicator

## Quick start

```bash
npm install
cp .env.example .env.local
# add your OPENAI_API_KEY to .env.local
npm run dev
```

Open `http://localhost:3000`

## Architecture

```txt
src/
  app/
    api/chat/route.ts        # API route with SSE streaming support
    layout.tsx
    page.tsx
  components/
    ChatClient.tsx            # Streaming-capable chat UI
  lib/
    core/
      orchestrator.ts         # Main orchestration — wires memory, tools, planner
      planner.ts              # Breaks complex requests into step-by-step plans
      executor.ts             # Validates and executes tool calls
      prompts.ts              # AAIS system prompt
      router.ts               # Model selection (env-configurable)
    memory/
      short-term.ts           # Sliding window + summarization
      long-term.ts            # TF-IDF vector similarity search
    tools/
      registry.ts             # 8 tools: calculator, datetime, text_utils, uuid, base64, json_format, echo, web_search
    types/
      chat.ts                 # Shared type definitions
backend/                      # Python multi-modal AI backend (Flask + PyTorch) — see backend/README.md
```

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI API key |
| `AAIS_MODEL` | No | `gpt-4.1-mini` | OpenAI model to use |

## Built-in tools

| Tool | Description |
|---|---|
| `calculator` | Math expressions with trig, log, etc. |
| `datetime` | Current date/time with timezone support |
| `text_utils` | Word count, slugify, reverse, uppercase, etc. |
| `uuid` | Generate UUIDs (v4) |
| `base64` | Encode/decode base64 |
| `json_format` | Pretty-print JSON |
| `echo` | Echo text (for testing) |
| `web_search` | Stub — guides you to add a real search API |

## Next moves

1. Store conversations in Postgres
2. Replace in-memory vectors with pgvector / Qdrant embeddings
3. Add permissioned tools (file I/O, API calls, code execution)
4. Connect the Python backend for local model inference
5. Add authentication and user sessions
