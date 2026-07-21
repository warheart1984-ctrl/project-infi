import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type OpenAiStyleResponse } from './helpers.js';

export interface LocalLlmBackendOptions {
  baseUrl: string;
  name?: string;
  model?: string;
  fetch?: typeof globalThis.fetch;
}

export class LocalLlmBackend implements CodingBackend {
  readonly name: string;
  readonly supports = { chat: true, code: true };

  private readonly baseUrl: string;
  private readonly model: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(baseUrl: string, options: Omit<LocalLlmBackendOptions, 'baseUrl'> = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.name = options.name ?? 'local-llm';
    this.model = options.model ?? 'local-model';
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  static fromOptions(options: LocalLlmBackendOptions): LocalLlmBackend {
    const { baseUrl, ...rest } = options;
    return new LocalLlmBackend(baseUrl, rest);
  }

  async chat(req: GovernedChatRequest) {
    const json = await postJson<OpenAiStyleResponse>(
      `${this.baseUrl}/v1/chat/completions`,
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
