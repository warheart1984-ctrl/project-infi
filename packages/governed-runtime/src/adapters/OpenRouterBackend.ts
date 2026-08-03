import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type OpenAiStyleResponse } from './helpers.js';
import { createLocalFetch } from './localFetch.js';

export interface OpenRouterBackendOptions {
  apiKey: string;
  /** Default: openrouter/free (Free Models Router). Override with any *:free slug. */
  model?: string;
  baseUrl?: string;
  name?: string;
  siteUrl?: string;
  siteName?: string;
  fetch?: typeof globalThis.fetch;
}

/**
 * OpenRouter cloud backend — prefer free models (`openrouter/free` or `vendor/model:free`).
 * Requires OPENROUTER_API_KEY. Image/video generation is not handled here (paid / separate APIs).
 */
export class OpenRouterBackend implements CodingBackend {
  readonly name: string;
  readonly supports = { chat: true, code: true };

  private readonly apiKey: string;
  private readonly model: string;
  private readonly baseUrl: string;
  private readonly siteUrl: string;
  private readonly siteName: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: OpenRouterBackendOptions) {
    this.apiKey = options.apiKey;
    this.model = options.model ?? process.env.OPENROUTER_MODEL ?? 'openrouter/free';
    this.baseUrl = (options.baseUrl ?? 'https://openrouter.ai/api/v1').replace(/\/$/, '');
    this.name = options.name ?? 'openrouter-free';
    this.siteUrl = options.siteUrl ?? process.env.OPENROUTER_SITE_URL ?? 'https://github.com/warheart1984-ctrl/AAES-OS';
    this.siteName = options.siteName ?? process.env.OPENROUTER_SITE_NAME ?? 'AAES-OS AAIS';
    this.fetchImpl = options.fetch ?? createLocalFetch();
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
      {
        Authorization: `Bearer ${this.apiKey}`,
        'HTTP-Referer': this.siteUrl,
        'X-Title': this.siteName,
      },
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
