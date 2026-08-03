import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type OpenAiStyleResponse } from './helpers.js';
import { createLocalFetch } from './localFetch.js';

export interface GroqBackendOptions {
  apiKey: string;
  model?: string;
  baseUrl?: string;
  name?: string;
  fetch?: typeof globalThis.fetch;
}

export class GroqBackend implements CodingBackend {
  readonly name: string;
  readonly supports = { chat: true, code: true };

  private readonly apiKey: string;
  private readonly model: string;
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(apiKey: string, options: Omit<GroqBackendOptions, 'apiKey'> = {}) {
    this.apiKey = apiKey;
    this.model = options.model ?? process.env.GROQ_MODEL ?? 'llama-3.3-70b-versatile';
    this.baseUrl = options.baseUrl ?? 'https://api.groq.com/openai/v1';
    this.name = options.name ?? 'groq';
    this.fetchImpl = options.fetch ?? createLocalFetch();
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
