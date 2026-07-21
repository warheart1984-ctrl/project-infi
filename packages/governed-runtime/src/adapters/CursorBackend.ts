import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type LocalApiResponse } from './helpers.js';

export interface CursorBackendOptions {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
}

export class CursorBackend implements CodingBackend {
  readonly name = 'cursor';
  readonly supports = { chat: true, code: true };

  private readonly baseUrl: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: CursorBackendOptions = {}) {
    this.baseUrl = options.baseUrl ?? 'http://localhost:5100';
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  async chat(req: GovernedChatRequest) {
    const json = await postJson<LocalApiResponse>(
      `${this.baseUrl}/chat`,
      {
        prompt: req.input.userContent,
        system: req.input.systemPrompt,
      },
      {},
      this.fetchImpl,
    );

    return buildChatResponse(
      req,
      this.name,
      json.text ?? '',
      json.tokensIn ?? 0,
      json.tokensOut ?? 0,
      json.latency ?? 0,
    );
  }
}
