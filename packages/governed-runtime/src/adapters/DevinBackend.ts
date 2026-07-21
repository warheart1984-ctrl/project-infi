import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson, type LocalApiResponse } from './helpers.js';

export interface DevinBackendOptions {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
}

export class DevinBackend implements CodingBackend {
  readonly name = 'devin';
  readonly supports = { chat: true, code: true, tools: true };

  private readonly baseUrl: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: DevinBackendOptions = {}) {
    this.baseUrl = options.baseUrl ?? 'http://localhost:8000';
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  async chat(req: GovernedChatRequest) {
    const json = await postJson<LocalApiResponse>(
      `${this.baseUrl}/devin/chat`,
      {
        input: req.input.userContent,
        system: req.input.systemPrompt,
      },
      {},
      this.fetchImpl,
    );

    return buildChatResponse(
      req,
      this.name,
      json.output ?? json.text ?? '',
      json.tokensIn ?? 0,
      json.tokensOut ?? 0,
      json.latency ?? 0,
    );
  }
}
