import type { ImageGenRequest, ImageGenResult, ImageProvider, ProviderEnv } from './types.js';

export interface StoryForgeConfig {
  baseUrl?: string;
  apiKey?: string;
  env?: ProviderEnv;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

const DEFAULT_BASE_URL = 'http://127.0.0.1:8080';
const DEFAULT_TIMEOUT_MS = 180_000;

export class StoryForgeProvider implements ImageProvider {
  readonly name = 'storyforge';
  readonly requiresApiKey = true;
  readonly configHelp =
    'StoryForge pipeline (Project Infinity sibling). Start Infinity service at G:\\Project-Infinity. Endpoints: /story/turn → /beatbox/generate → /speakers/synthesize. Required: set STORYFORGE_API_KEY (Bearer token) or STORYFORGE_BASE_URL to your Infinity service URL.';

  private readonly baseUrl: string;
  private readonly apiKey: string | undefined;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;

  constructor(config: StoryForgeConfig = {}) {
    const env = config.env ?? process.env;
    this.baseUrl = (config.baseUrl ?? env.STORYFORGE_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/+$/, '');
    this.apiKey = config.apiKey ?? env.STORYFORGE_API_KEY;
    this.fetchImpl = config.fetchImpl ?? fetch;
    this.timeoutMs = config.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  }

  get configured(): boolean {
    return true;
  }

  listModels(): Promise<string[]> {
    return Promise.resolve([
      'storyforge-full-pipeline',
      'storyforge-text-only',
      'beatbox-audio',
      'speakers-tts',
    ]);
  }

  async generate(
    request: ImageGenRequest,
    options?: { signal?: AbortSignal },
  ): Promise<ImageGenResult> {
    const prompt = request.prompt.trim();
    if (!prompt) {
      throw new Error('StoryForge provider requires a non-empty prompt');
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);
    options?.signal?.addEventListener('abort', () => controller.abort());

    try {
      const storyResult = await this.callStoryTurn(prompt, controller.signal);
      
      const audioResult = await this.callBeatbox(storyResult.narrative, controller.signal);
      
      const speechResult = await this.callSpeakers(audioResult.audioUrl, controller.signal);

      const audioResponse = await this.fetchWithAuth(speechResult.audioUrl, {
        method: 'GET',
        signal: controller.signal,
      });
      if (!audioResponse.ok) {
        throw new Error(`Failed to download final audio (${audioResponse.status})`);
      }
      const audioBytes = Buffer.from(await audioResponse.arrayBuffer());
      
      const contentType = audioResponse.headers.get('content-type') ?? 'audio/wav';

      return {
        provider: this.name,
        model: request.model ?? 'storyforge-full-pipeline',
        contentType,
        bytes: audioBytes,
      };
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private async callStoryTurn(prompt: string, signal: AbortSignal): Promise<{ narrative: string }> {
    const response = await this.fetchWithAuth(`${this.baseUrl}/story/turn`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ prompt, mode: 'narrative' }),
      signal,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      throw new Error(`StoryForge /story/turn failed (${response.status}): ${detail}`);
    }
    return response.json();
  }

  private async callBeatbox(narrative: string, signal: AbortSignal): Promise<{ audioUrl: string }> {
    const response = await this.fetchWithAuth(`${this.baseUrl}/beatbox/generate`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ text: narrative, style: 'ambient' }),
      signal,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      throw new Error(`Beatbox failed (${response.status}): ${detail}`);
    }
    return response.json();
  }

  private async callSpeakers(audioUrl: string, signal: AbortSignal): Promise<{ audioUrl: string }> {
    const response = await this.fetchWithAuth(`${this.baseUrl}/speakers/synthesize`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ audioUrl, voice: 'narrator' }),
      signal,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      throw new Error(`Speakers failed (${response.status}): ${detail}`);
    }
    return response.json();
  }

  private async fetchWithAuth(url: string, init: RequestInit): Promise<Response> {
    const headers: Record<string, string> = {
      'content-type': 'application/json',
      ...(init.headers as Record<string, string>),
    };
    if (this.apiKey) {
      headers['authorization'] = `Bearer ${this.apiKey}`;
    }
    return this.fetchImpl(url, { ...init, headers });
  }
}