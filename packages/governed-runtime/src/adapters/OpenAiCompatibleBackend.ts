import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type OpenAiStyleResponse } from './helpers.js';

export interface OpenAiCompatibleBackendOptions {
  name: string;
  baseUrl: string;
  model?: string;
  apiKey?: string;
  fetch?: typeof globalThis.fetch;
}

/** Generic adapter for any free/local OpenAI-compatible agent (vLLM, text-gen-webui, etc.). */
export class OpenAiCompatibleBackend implements CodingBackend {
  readonly name: string;
  readonly supports = { chat: true, code: true };

  private readonly baseUrl: string;
  private readonly model: string;
  private readonly apiKey?: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: OpenAiCompatibleBackendOptions) {
    this.name = options.name;
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.model = options.model ?? 'default';
    this.apiKey = options.apiKey;
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  async chat(req: GovernedChatRequest) {
    const headers: Record<string, string> = {};
    if (this.apiKey) {
      headers.Authorization = `Bearer ${this.apiKey}`;
    }

    const json = await postJson<OpenAiStyleResponse>(
      `${this.baseUrl}/v1/chat/completions`,
      {
        model: this.model,
        messages: [
          { role: 'system', content: req.input.systemPrompt },
          { role: 'user', content: req.input.userContent },
        ],
      },
      headers,
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
