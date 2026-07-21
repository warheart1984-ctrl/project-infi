import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type OpenAiStyleResponse } from './helpers.js';

export interface DeepSeekCoderBackendOptions {
  baseUrl?: string;
  model?: string;
  fetch?: typeof globalThis.fetch;
}

export class DeepSeekCoderBackend implements CodingBackend {
  readonly name = 'deepseek-coder';
  readonly supports = { chat: true, code: true };

  private readonly baseUrl: string;
  private readonly model: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: DeepSeekCoderBackendOptions = {}) {
    this.baseUrl = options.baseUrl ?? 'http://localhost:11434/v1';
    this.model = options.model ?? 'deepseek-coder';
    this.fetchImpl = options.fetch ?? globalThis.fetch;
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
      {},
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
