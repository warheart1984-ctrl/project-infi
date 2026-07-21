import { CursorBackend } from '../adapters/CursorBackend.js';
import { CursorSdkBackend } from '../adapters/CursorSdkBackend.js';
import { DeepSeekCoderBackend } from '../adapters/DeepSeekCoderBackend.js';
import { DevinBackend } from '../adapters/DevinBackend.js';
import { LmStudioBackend } from '../adapters/LmStudioBackend.js';
import { LocalLlmBackend } from '../adapters/LocalLlmBackend.js';
import { OllamaBackend } from '../adapters/OllamaBackend.js';
import { OpenAiCompatibleBackend } from '../adapters/OpenAiCompatibleBackend.js';
import type { CodingBackend } from '../types.js';

export interface AgentEndpoint {
  name: string;
  baseUrl: string;
  model?: string;
  kind?: 'ollama' | 'openai-compatible' | 'cursor' | 'cursor-sdk' | 'devin';
  apiKey?: string;
  cwd?: string;
}

export interface DiscoveryOptions {
  fetch?: typeof globalThis.fetch;
  timeoutMs?: number;
  ollamaUrl?: string;
  lmStudioUrl?: string;
  cursorUrl?: string;
  cursorApiKey?: string;
  cursorCwd?: string;
  cursorModel?: string;
  devinUrl?: string;
  localLlmUrl?: string;
  extraEndpoints?: AgentEndpoint[];
  /** Skip network probes and use only manually supplied backends. */
  backends?: CodingBackend[];
}

export interface DiscoveredAgent {
  name: string;
  url: string;
  models?: string[];
}

export interface DiscoveryResult {
  backends: CodingBackend[];
  available: DiscoveredAgent[];
  skipped: Array<{ name: string; url: string; reason: string }>;
}

interface OllamaTagsResponse {
  models?: Array<{ name: string }>;
}

interface OpenAiModelsResponse {
  data?: Array<{ id: string }>;
}

const CODER_MODEL_HINTS = ['coder', 'code', 'deepseek', 'qwen', 'starcoder', 'phi', 'llama'];

function pickCoderModel(models: string[]): string | undefined {
  const lower = models.map((m) => m.toLowerCase());
  for (const hint of CODER_MODEL_HINTS) {
    const idx = lower.findIndex((m) => m.includes(hint));
    if (idx >= 0) return models[idx];
  }
  return models[0];
}

async function probeGet(
  url: string,
  fetchImpl: typeof globalThis.fetch,
  timeoutMs: number,
): Promise<Response | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetchImpl(url, { signal: controller.signal });
    return res.ok ? res : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

function backendFromEndpoint(endpoint: AgentEndpoint, fetchImpl: typeof globalThis.fetch): CodingBackend {
  switch (endpoint.kind ?? 'openai-compatible') {
    case 'ollama':
      return new OllamaBackend({ baseUrl: endpoint.baseUrl, model: endpoint.model, name: endpoint.name, fetch: fetchImpl });
    case 'cursor':
      return new CursorBackend({ baseUrl: endpoint.baseUrl, fetch: fetchImpl });
    case 'cursor-sdk':
      return new CursorSdkBackend({
        apiKey: endpoint.apiKey,
        cwd: endpoint.cwd ?? process.cwd(),
        model: endpoint.model,
      });
    case 'devin':
      return new DevinBackend({ baseUrl: endpoint.baseUrl, fetch: fetchImpl });
    default:
      return new OpenAiCompatibleBackend({
        name: endpoint.name,
        baseUrl: endpoint.baseUrl,
        model: endpoint.model,
        fetch: fetchImpl,
      });
  }
}

export async function discoverFreeBackends(options: DiscoveryOptions = {}): Promise<DiscoveryResult> {
  const fetchImpl = options.fetch ?? globalThis.fetch;
  const timeoutMs = options.timeoutMs ?? 1500;

  if (options.backends && options.backends.length > 0) {
    return {
      backends: options.backends,
      available: options.backends.map((b) => ({ name: b.name, url: 'manual' })),
      skipped: [],
    };
  }

  const backends: CodingBackend[] = [];
  const available: DiscoveredAgent[] = [];
  const skipped: DiscoveryResult['skipped'] = [];

  const ollamaUrl = (options.ollamaUrl ?? process.env.OLLAMA_HOST ?? 'http://127.0.0.1:11434').replace(/\/$/, '');
  const ollamaRes = await probeGet(`${ollamaUrl}/api/tags`, fetchImpl, timeoutMs);
  if (ollamaRes) {
    const tags = (await ollamaRes.json()) as OllamaTagsResponse;
    const models = (tags.models ?? []).map((m) => m.name);
    const model = pickCoderModel(models) ?? 'qwen2.5-coder:3b';
    backends.push(new OllamaBackend({ baseUrl: ollamaUrl, model, fetch: fetchImpl }));
    available.push({ name: 'ollama', url: ollamaUrl, models });

    if (models.some((m) => m.toLowerCase().includes('deepseek'))) {
      backends.push(
        new DeepSeekCoderBackend({
          baseUrl: `${ollamaUrl}/v1`,
          model: pickCoderModel(models.filter((m) => m.toLowerCase().includes('deepseek'))) ?? 'deepseek-coder',
          fetch: fetchImpl,
        }),
      );
      available.push({ name: 'deepseek-coder', url: ollamaUrl, models });
    }
  } else {
    skipped.push({ name: 'ollama', url: ollamaUrl, reason: 'not reachable' });
  }

  const lmStudioUrl = (options.lmStudioUrl ?? process.env.LM_STUDIO_URL ?? 'http://127.0.0.1:1234').replace(/\/$/, '');
  const lmRes = await probeGet(`${lmStudioUrl}/v1/models`, fetchImpl, timeoutMs);
  if (lmRes) {
    const body = (await lmRes.json()) as OpenAiModelsResponse;
    const models = (body.data ?? []).map((m) => m.id);
    const model = pickCoderModel(models) ?? 'local-model';
    backends.push(new LmStudioBackend({ baseUrl: lmStudioUrl, model, fetch: fetchImpl }));
    available.push({ name: 'lm-studio', url: lmStudioUrl, models });
  } else {
    skipped.push({ name: 'lm-studio', url: lmStudioUrl, reason: 'not reachable' });
  }

  const cursorApiKey = options.cursorApiKey ?? process.env.CURSOR_API_KEY;
  const cursorCwd = options.cursorCwd ?? process.env.CURSOR_CWD ?? process.cwd();
  const cursorModel = options.cursorModel ?? process.env.CURSOR_MODEL ?? 'composer-2.5';
  if (cursorApiKey) {
    backends.push(new CursorSdkBackend({ apiKey: cursorApiKey, cwd: cursorCwd, model: cursorModel }));
    available.push({ name: 'cursor', url: `cursor-sdk:${cursorCwd}`, models: [cursorModel] });
  } else {
    const cursorUrl = (options.cursorUrl ?? 'http://127.0.0.1:5100').replace(/\/$/, '');
    const cursorRes = await probeGet(`${cursorUrl}/health`, fetchImpl, timeoutMs);
    if (cursorRes) {
      backends.push(new CursorBackend({ baseUrl: cursorUrl, fetch: fetchImpl }));
      available.push({ name: 'cursor', url: cursorUrl });
    } else {
      skipped.push({ name: 'cursor', url: cursorUrl, reason: 'CURSOR_API_KEY not set and bridge not reachable' });
    }
  }

  const devinUrl = (options.devinUrl ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
  const devinRes = await probeGet(`${devinUrl}/health`, fetchImpl, timeoutMs);
  if (devinRes) {
    backends.push(new DevinBackend({ baseUrl: devinUrl, fetch: fetchImpl }));
    available.push({ name: 'devin', url: devinUrl });
  } else {
    skipped.push({ name: 'devin', url: devinUrl, reason: 'not reachable' });
  }

  const localUrl = (options.localLlmUrl ?? 'http://127.0.0.1:8080').replace(/\/$/, '');
  const localRes = await probeGet(`${localUrl}/v1/models`, fetchImpl, timeoutMs);
  if (localRes) {
    const body = (await localRes.json()) as OpenAiModelsResponse;
    const models = (body.data ?? []).map((m) => m.id);
    backends.push(
      new LocalLlmBackend(localUrl, {
        model: pickCoderModel(models) ?? 'local-model',
        fetch: fetchImpl,
      }),
    );
    available.push({ name: 'local-llm', url: localUrl, models });
  } else {
    skipped.push({ name: 'local-llm', url: localUrl, reason: 'not reachable' });
  }

  for (const endpoint of options.extraEndpoints ?? []) {
    backends.push(backendFromEndpoint(endpoint, fetchImpl));
    available.push({ name: endpoint.name, url: endpoint.baseUrl });
  }

  return { backends, available, skipped };
}

export function requireFreeBackends(result: DiscoveryResult): CodingBackend[] {
  if (result.backends.length === 0) {
    throw new Error(
      'No free local agents found. Start one of: Ollama (ollama serve), LM Studio, Cursor SDK (CURSOR_API_KEY), Cursor local API, or Devin local API. ' +
        'Then run discoverFreeBackends() again.',
    );
  }
  return result.backends;
}
