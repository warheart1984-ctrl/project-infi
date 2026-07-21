import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type OpenAiStyleResponse } from './helpers.js';

export interface LmStudioBackendOptions {
  baseUrl?: string;
  model?: string;
  name?: string;
  fetch?: typeof globalThis.fetch;
}

export class LmStudioBackend implements CodingBackend {
  readonly name: string;
  readonly supports = { chat: true, code: true };

  private readonly baseUrl: string;
  private readonly model: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: LmStudioBackendOptions = {}) {
    this.baseUrl = (options.baseUrl ?? process.env.LM_STUDIO_URL ?? 'http://127.0.0.1:1234').replace(
      /\/$/,
      '',
    );
    this.model = options.model ?? process.env.LM_STUDIO_MODEL ?? 'local-model';
    this.name = options.name ?? 'lm-studio';
    this.fetchImpl = options.fetch ?? globalThis.fetch;
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
