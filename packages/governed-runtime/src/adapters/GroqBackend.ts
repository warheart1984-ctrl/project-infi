import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type OpenAiStyleResponse } from './helpers.js';

export interface GroqBackendOptions {
  apiKey: string;
  model?: string;
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
}

export class GroqBackend implements CodingBackend {
  readonly name = 'groq-llama3-70b';
  readonly supports = { chat: true, code: true };

  private readonly apiKey: string;
  private readonly model: string;
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(apiKey: string, options: Omit<GroqBackendOptions, 'apiKey'> = {}) {
    this.apiKey = apiKey;
    this.model = options.model ?? 'llama3-70b-8192';
    this.baseUrl = options.baseUrl ?? 'https://api.groq.com/openai/v1';
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  static fromOptions(options: GroqBackendOptions): GroqBackend {
    const { apiKey, ...rest } = options;
    return new GroqBackend(apiKey, rest);
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
