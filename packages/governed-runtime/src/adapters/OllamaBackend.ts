import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse, postJson } from './helpers.js';

export interface OllamaBackendOptions {
  baseUrl?: string;
  model?: string;
  name?: string;
  fetch?: typeof globalThis.fetch;
}

interface OllamaChatResponse {
  message?: { content?: string };
  prompt_eval_count?: number;
  eval_count?: number;
}

export class OllamaBackend implements CodingBackend {
  readonly name: string;
  readonly supports = { chat: true, code: true };

  private readonly baseUrl: string;
  private readonly model: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: OllamaBackendOptions = {}) {
    this.baseUrl = (options.baseUrl ?? process.env.OLLAMA_HOST ?? 'http://127.0.0.1:11434').replace(
      /\/$/,
      '',
    );
    this.model = options.model ?? process.env.OLLAMA_MODEL ?? 'qwen2.5-coder:3b';
    this.name = options.name ?? 'ollama';
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  async chat(req: GovernedChatRequest) {
    const json = await postJson<OllamaChatResponse>(
      `${this.baseUrl}/api/chat`,
      {
        model: this.model,
        messages: [
          { role: 'system', content: req.input.systemPrompt },
          { role: 'user', content: req.input.userContent },
        ],
        stream: false,
      },
      {},
      this.fetchImpl,
    );

    return buildChatResponse(
      req,
      this.name,
      json.message?.content ?? '',
      json.prompt_eval_count ?? 0,
      json.eval_count ?? 0,
    );
  }
}
