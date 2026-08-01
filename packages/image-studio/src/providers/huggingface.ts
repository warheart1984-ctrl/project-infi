import { detectImageType } from '../detectImageType.js';
import { resolveReferenceBase64 } from './reference.js';
import type { ImageGenRequest, ImageGenResult, ImageProvider, ProviderEnv } from './types.js';

const HUGGING_FACE_BASE_URL = 'https://router.huggingface.co/hf-inference';
const HUGGING_FACE_DEFAULT_MODEL = 'black-forest-labs/FLUX.1-Kontext-dev';

export interface HuggingFaceConfig {
  apiToken?: string;
  env?: ProviderEnv;
  fetchImpl?: typeof fetch;
}

export class HuggingFaceProvider implements ImageProvider {
  readonly name = 'huggingface';
  readonly requiresApiKey = true;
  readonly configHelp =
    'Set HF_TOKEN (free Hugging Face account, token with "Inference Providers" permission). Free tier: monthly inference credits.';

  private readonly apiToken: string | undefined;
  private readonly fetchImpl: typeof fetch;

  constructor(config: HuggingFaceConfig = {}) {
    const env = config.env ?? process.env;
    this.apiToken = config.apiToken ?? env.HF_TOKEN;
    this.fetchImpl = config.fetchImpl ?? fetch;
  }

  get configured(): boolean {
    return Boolean(this.apiToken);
  }

  listModels(): Promise<string[]> {
    return Promise.resolve([HUGGING_FACE_DEFAULT_MODEL]);
  }

  async generate(
    request: ImageGenRequest,
    options?: { signal?: AbortSignal },
  ): Promise<ImageGenResult> {
    if (!this.configured) {
      throw new Error(`Hugging Face provider is not configured. ${this.configHelp}`);
    }
    const prompt = request.prompt.trim();
    if (!prompt) {
      throw new Error('Hugging Face requires a non-empty prompt');
    }

    const model = request.model?.trim() || HUGGING_FACE_DEFAULT_MODEL;
    const inputs = await resolveReferenceBase64(request.referenceImage, this.fetchImpl);

    const payload: Record<string, unknown> = {
      inputs,
      parameters: { prompt },
    };
    if (request.width || request.height) {
      payload.parameters = {
        prompt,
        target_size: {
          width: request.width ?? 1024,
          height: request.height ?? 1024,
        },
      };
    }

    const url = `${HUGGING_FACE_BASE_URL}/models/${encodeURIComponent(model)}/image-to-image`;
    const response = await this.fetchImpl(url, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${this.apiToken}`,
        'content-type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: options?.signal,
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      throw new Error(`Hugging Face request failed (${response.status}): ${detail.slice(0, 500) || 'no details'}`);
    }

    const bytes = Buffer.from(await response.arrayBuffer());
    const contentType =
      detectImageType(bytes) ?? response.headers.get('content-type') ?? 'application/octet-stream';

    return {
      provider: this.name,
      model,
      contentType,
      bytes,
    };
  }
}
