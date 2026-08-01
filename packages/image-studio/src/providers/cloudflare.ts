import { detectImageType } from '../detectImageType.js';
import { resolveReferenceBase64 } from './reference.js';
import type { ImageGenRequest, ImageGenResult, ImageProvider, ProviderEnv } from './types.js';

const CLOUDFLARE_BASE_URL = 'https://api.cloudflare.com/client/v4';
const CLOUDFLARE_IMG2IMG_MODEL = '@cf/runwayml/stable-diffusion-v1-5-img2img';

export interface CloudflareConfig {
  accountId?: string;
  apiToken?: string;
  env?: ProviderEnv;
  fetchImpl?: typeof fetch;
}

export class CloudflareProvider implements ImageProvider {
  readonly name = 'cloudflare';
  readonly requiresApiKey = true;
  readonly configHelp =
    'Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN (free Cloudflare account). Free tier: ~10k neurons/day.';

  private readonly accountId: string | undefined;
  private readonly apiToken: string | undefined;
  private readonly fetchImpl: typeof fetch;

  constructor(config: CloudflareConfig = {}) {
    const env = config.env ?? process.env;
    this.accountId = config.accountId ?? env.CLOUDFLARE_ACCOUNT_ID ?? env.CF_ACCOUNT_ID;
    this.apiToken = config.apiToken ?? env.CLOUDFLARE_API_TOKEN ?? env.CF_API_TOKEN;
    this.fetchImpl = config.fetchImpl ?? fetch;
  }

  get configured(): boolean {
    return Boolean(this.accountId && this.apiToken);
  }

  listModels(): Promise<string[]> {
    return Promise.resolve([CLOUDFLARE_IMG2IMG_MODEL]);
  }

  async generate(
    request: ImageGenRequest,
    options?: { signal?: AbortSignal },
  ): Promise<ImageGenResult> {
    if (!this.configured) {
      throw new Error(`Cloudflare provider is not configured. ${this.configHelp}`);
    }
    const prompt = request.prompt.trim();
    if (!prompt) {
      throw new Error('Cloudflare requires a non-empty prompt');
    }

    const imageB64 = await resolveReferenceBase64(request.referenceImage, this.fetchImpl);

    const body: Record<string, unknown> = {
      prompt,
      image_b64: imageB64,
    };
    if (request.width) {
      body.width = clampDimension(request.width);
    }
    if (request.height) {
      body.height = clampDimension(request.height);
    }
    if (request.seed !== undefined) {
      body.seed = request.seed;
    }

    const url = `${CLOUDFLARE_BASE_URL}/accounts/${this.accountId}/ai/run/${CLOUDFLARE_IMG2IMG_MODEL}`;
    const response = await this.fetchImpl(url, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${this.apiToken}`,
        'content-type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: options?.signal,
    });

    const payload = (await response.json().catch(() => null)) as
      | { success?: boolean; errors?: unknown[]; messages?: unknown[]; result?: { image?: string } }
      | null;

    if (!response.ok || payload?.success === false) {
      throw new Error(`Cloudflare request failed (${response.status}): ${describeCloudflareErrors(payload)}`);
    }

    const imageB64Out = payload?.result?.image;
    if (!imageB64Out) {
      throw new Error('Cloudflare returned no image in the response');
    }

    const bytes = Buffer.from(imageB64Out, 'base64');
    if (bytes.length === 0) {
      throw new Error('Cloudflare returned an empty image payload');
    }
    const contentType = detectImageType(bytes) ?? 'image/png';

    return {
      provider: this.name,
      model: CLOUDFLARE_IMG2IMG_MODEL,
      contentType,
      bytes,
    };
  }
}

function clampDimension(value: number): number {
  if (!Number.isFinite(value)) {
    return 512;
  }
  return Math.min(2048, Math.max(256, Math.floor(value)));
}

function describeCloudflareErrors(
  payload: { errors?: unknown[]; messages?: unknown[] } | null,
): string {
  if (!payload) {
    return 'no details';
  }
  const entries = [...(payload.errors ?? []), ...(payload.messages ?? [])];
  if (entries.length === 0) {
    return 'no details';
  }
  return JSON.stringify(entries).slice(0, 500);
}
