import type { ImageGenRequest, ImageGenResult, ImageProvider } from './types.js';
import { detectImageType } from '../detectImageType.js';

const POLLINATIONS_BASE_URL = 'https://image.pollinations.ai';
const FALLBACK_MODELS = ['sana'];

export class PollinationsProvider implements ImageProvider {
  readonly name = 'pollinations';
  readonly requiresApiKey = false;
  readonly configured = true;

  constructor(
    private readonly baseUrl: string = POLLINATIONS_BASE_URL,
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  async listModels(options?: { signal?: AbortSignal }): Promise<string[]> {
    try {
      const response = await this.fetchImpl(`${this.baseUrl}/models`, { signal: options?.signal });
      if (!response.ok) {
        return [...FALLBACK_MODELS];
      }
      const data = (await response.json()) as unknown;
      if (!Array.isArray(data)) {
        return [...FALLBACK_MODELS];
      }
      const models = data.filter((entry): entry is string => typeof entry === 'string' && entry.length > 0);
      return models.length > 0 ? models : [...FALLBACK_MODELS];
    } catch {
      return [...FALLBACK_MODELS];
    }
  }

  async generate(
    request: ImageGenRequest,
    options?: { signal?: AbortSignal },
  ): Promise<ImageGenResult> {
    const prompt = request.prompt.trim();
    if (!prompt) {
      throw new Error('Pollinations requires a non-empty prompt');
    }

    const model = request.model?.trim() || FALLBACK_MODELS[0];
    const params = new URLSearchParams();
    params.set('model', model);
    params.set('nologo', request.nologo ? 'true' : 'false');
    if (request.width) {
      params.set('width', String(request.width));
    }
    if (request.height) {
      params.set('height', String(request.height));
    }
    if (request.seed !== undefined) {
      params.set('seed', String(request.seed));
    }
    const reference = request.referenceImage
      ? request.referenceImage.kind === 'url'
        ? request.referenceImage.url
        : request.referenceImage.dataUrl
      : undefined;
    if (reference) {
      params.set('image', reference);
    }

    const url = `${this.baseUrl}/prompt/${encodeURIComponent(prompt)}?${params.toString()}`;
    const response = await this.fetchImpl(url, { signal: options?.signal });

    if (!response.ok) {
      throw new Error(await describePollinationsError(response));
    }

    const bytes = Buffer.from(await response.arrayBuffer());
    const contentType = detectImageType(bytes) ?? response.headers.get('content-type') ?? 'application/octet-stream';

    return {
      provider: this.name,
      model,
      contentType,
      bytes,
    };
  }
}

async function describePollinationsError(response: Response): Promise<string> {
  const detail = await response.text().catch(() => '');
  let message = detail;
  try {
    const parsed = JSON.parse(detail) as Record<string, unknown>;
    message =
      typeof parsed.message === 'string'
        ? parsed.message
        : typeof parsed.error === 'string'
          ? parsed.error
          : detail;
  } catch {
    // not JSON, keep raw text
  }
  const trimmed = message.trim().slice(0, 500);
  return `Pollinations request failed (${response.status}): ${trimmed || 'no details'}`;
}
