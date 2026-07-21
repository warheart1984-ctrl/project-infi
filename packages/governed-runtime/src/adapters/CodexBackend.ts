import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type OpenAiStyleResponse } from './helpers.js';

export interface CodexBackendOptions {
  apiKey: string;
  model?: string;
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
}

export class CodexBackend implements CodingBackend {
  readonly name = 'codex';
  readonly supports = { chat: true, code: true };

  private readonly model: string;
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(private readonly apiKey: string, options: Omit<CodexBackendOptions, 'apiKey'> = {}) {
    this.model = options.model ?? 'gpt-4o-mini';
    this.baseUrl = options.baseUrl ?? 'https://api.openai.com/v1';
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  static fromOptions(options: CodexBackendOptions): CodexBackend {
    const { apiKey, ...rest } = options;
    return new CodexBackend(apiKey, rest);
  }

  async chat(req: GovernedChatRequest) {
    const json = await postJson<OpenAiStyleResponse>(
      `${this.baseUrl}/chat/completions`,
      {
        model: this.model,
        messages: [
          { role: 'system', content: req.input.systemPrompt },
          { role: 'user', content: req.input.userContent },
        ],
      },
      { Authorization: `Bearer ${this.apiKey}` },
      this.fetchImpl,
    );

    return buildChatResponse(
      req,
      this.name,
      json.choices?.[0]?.message?.content ?? '',
      json.usage?.prompt_tokens ?? 0,
      json.usage?.completion_tokens ?? 0,
    );
  }
}
