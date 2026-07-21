import type { CodingBackend, GovernedChatRequest } from '../types.js';
import { buildChatResponse } from './helpers.js';

export type CursorRunStatus = 'finished' | 'error' | 'cancelled';

export interface CursorTokenUsage {
  inputTokens: number;
  outputTokens: number;
  cacheReadTokens?: number;
  cacheWriteTokens?: number;
  totalTokens?: number;
  reasoningTokens?: number;
}

export interface CursorPromptResult {
  id: string;
  requestId?: string;
  status: CursorRunStatus;
  result?: string;
  durationMs?: number;
  usage?: CursorTokenUsage;
}

export interface CursorPromptOptions {
  apiKey: string;
  model: { id: string };
  local: { cwd: string };
}

export interface CursorSdkModule {
  Agent: {
    prompt(prompt: string, options: CursorPromptOptions): Promise<CursorPromptResult>;
  };
  CursorAgentError?: new (...args: unknown[]) => Error;
}

export interface CursorSdkBackendOptions {
  apiKey?: string;
  cwd: string;
  model?: string;
  cursorModule?: CursorSdkModule;
  loadCursorModule?: () => Promise<CursorSdkModule>;
}

export class CursorSdkBackend implements CodingBackend {
  readonly name = 'cursor';
  readonly supports = { chat: true, code: true, tools: true };

  private readonly apiKey: string;
  private readonly cwd: string;
  private readonly model: string;
  private readonly cursorModule?: CursorSdkModule;
  private readonly loadCursorModule?: () => Promise<CursorSdkModule>;

  constructor(options: CursorSdkBackendOptions) {
    const apiKey = options.apiKey ?? process.env.CURSOR_API_KEY;
    if (!apiKey) {
      throw new Error('CursorSdkBackend requires CURSOR_API_KEY or options.apiKey');
    }

    this.apiKey = apiKey;
    this.cwd = options.cwd;
    this.model = options.model ?? 'composer-2.5';
    this.cursorModule = options.cursorModule;
    this.loadCursorModule = options.loadCursorModule;
  }

  async chat(req: GovernedChatRequest) {
    const cursor = await this.resolveCursorModule();
    const prompt = this.buildPrompt(req);
    const start = Date.now();

    try {
      const result = await cursor.Agent.prompt(prompt, {
        apiKey: this.apiKey,
        model: { id: this.model },
        local: { cwd: this.cwd },
      });

      if (result.status !== 'finished') {
        throw new Error(`Cursor run did not finish (${result.status}): ${result.id}`);
      }

      return buildChatResponse(
        req,
        this.name,
        result.result ?? '',
        result.usage?.inputTokens ?? 0,
        result.usage?.outputTokens ?? 0,
        result.durationMs ?? Date.now() - start,
      );
    } catch (err) {
      const CursorAgentError = cursor.CursorAgentError;
      if (CursorAgentError && err instanceof CursorAgentError) {
        throw new Error(`Cursor startup failed: ${err.message}`);
      }
      throw err;
    }
  }

  private buildPrompt(req: GovernedChatRequest): string {
    return [req.input.systemPrompt, req.input.context, req.input.userContent]
      .filter((part): part is string => Boolean(part && part.trim()))
      .join('\n\n');
  }

  private async resolveCursorModule(): Promise<CursorSdkModule> {
    if (this.cursorModule) {
      return this.cursorModule;
    }
    if (this.loadCursorModule) {
      return this.loadCursorModule();
    }

    const packageName = '@cursor/sdk';
    return (await import(packageName)) as CursorSdkModule;
  }
}