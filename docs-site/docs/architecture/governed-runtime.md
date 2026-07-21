# Governed Runtime

The `@aaes-os/governed-runtime` package provides the universal coding adapter layer.

## CodingBackend Interface

Every coding engine implements:

```ts
interface CodingBackend {
  name: string;
  supports: { chat: boolean; code: boolean; tools?: boolean };
  chat(req: GovernedChatRequest): Promise<GovernedChatResponse>;
  completeCode?(req: CodeCompletionRequest): Promise<CodeCompletionResponse>;
}
```

## CodingRouter

The router:

1. Matches policies against the request governance context
2. Resolves the best backend (preferred → first allowed → first available)
3. Enforces guardrails (identity roles, token limits)
4. Annotates the response with matched policy IDs

## Available Backends

| Backend | Name | Use Case |
|---------|------|----------|
| CodexBackend | `codex` | OpenAI-compatible cloud |
| CursorBackend | `cursor` | Local Cursor API |
| DevinBackend | `devin` | Agentic tool-use |
| DeepSeekCoderBackend | `deepseek-coder` | Multi-file reasoning |
| GroqBackend | `groq-llama3-70b` | Fast general coding |
| LocalLlmBackend | `local-llm` | Sensitive / proprietary code |
