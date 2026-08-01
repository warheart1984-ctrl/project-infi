import { detectImageType } from '../detectImageType.js';
import { dataUrlToBase64 } from './reference.js';
import type { ImageGenRequest, ImageGenResult, ImageProvider, ProviderEnv, ReferenceImage } from './types.js';

const GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta';
const DEFAULT_MODEL = 'gemini-2.5-flash-image';

export interface GeminiConfig {
  apiKey?: string;
  model?: string;
  env?: ProviderEnv;
  fetchImpl?: typeof fetch;
  baseUrl?: string;
}

interface GeminiInlineData {
  mimeType?: string;
  mime_type?: string;
  data?: string;
}

interface GeminiPart {
  text?: string;
  inlineData?: GeminiInlineData;
  inline_data?: GeminiInlineData;
}

interface GeminiGenerateResponse {
  error?: { message?: string; status?: string; code?: number };
  candidates?: Array<{
    content?: {
      parts?: GeminiPart[];
    };
  }>;
}

export class GeminiProvider implements ImageProvider {
  readonly name = 'gemini';
  readonly requiresApiKey = true;
  readonly configHelp =
    'Set GEMINI_API_KEY or GOOGLE_API_KEY (Google AI Studio). Free-tier image quotas apply; see ai.google.dev.';

  private readonly apiKey: string | undefined;
  private readonly model: string;
  private readonly fetchImpl: typeof fetch;
  private readonly baseUrl: string;

  constructor(config: GeminiConfig = {}) {
    const env = config.env ?? process.env;
    this.apiKey = config.apiKey ?? env.GEMINI_API_KEY ?? env.GOOGLE_API_KEY;
    this.model =
      config.model?.trim() ||
      env.GEMINI_IMAGE_MODEL?.trim() ||
      DEFAULT_MODEL;
    this.fetchImpl = config.fetchImpl ?? fetch;
    this.baseUrl = (config.baseUrl ?? GEMINI_BASE_URL).replace(/\/$/, '');
  }

  get configured(): boolean {
    return Boolean(this.apiKey);
  }

  listModels(): Promise<string[]> {
    return Promise.resolve([this.model, 'gemini-2.5-flash-image', 'gemini-2.0-flash-preview-image-generation']);
  }

  async generate(
    request: ImageGenRequest,
    options?: { signal?: AbortSignal },
  ): Promise<ImageGenResult> {
    if (!this.configured) {
      throw new Error(`Gemini provider is not configured. ${this.configHelp}`);
    }

    const prompt = request.prompt.trim();
    if (!prompt) {
      throw new Error('Gemini requires a non-empty prompt');
    }

    const model = request.model?.trim() || this.model;
    const parts: GeminiPart[] = [{ text: prompt }];
    const referencePart = await this.buildReferencePart(request.referenceImage, options?.signal);
    if (referencePart) {
      parts.push(referencePart);
    }

    const url = `${this.baseUrl}/models/${encodeURIComponent(model)}:generateContent`;
    const response = await this.fetchImpl(url, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-goog-api-key': this.apiKey as string,
      },
      body: JSON.stringify({
        contents: [{ role: 'user', parts }],
        generationConfig: {
          responseModalities: ['TEXT', 'IMAGE'],
        },
      }),
      signal: options?.signal,
    });

    const payload = (await response.json().catch(() => null)) as GeminiGenerateResponse | null;
    if (!response.ok) {
      throw new Error(`Gemini request failed (${response.status}): ${describeGeminiError(payload)}`);
    }

    const imagePart = findInlineImagePart(payload);
    if (!imagePart) {
      throw new Error('Gemini returned no image in the response');
    }

    const bytes = Buffer.from(imagePart.data, 'base64');
    if (bytes.length === 0) {
      throw new Error('Gemini returned an empty image payload');
    }

    const contentType =
      detectImageType(bytes) ?? imagePart.mimeType ?? 'image/png';

    return {
      provider: this.name,
      model,
      contentType,
      bytes,
    };
  }

  private async buildReferencePart(
    reference: ReferenceImage | undefined,
    signal?: AbortSignal,
  ): Promise<GeminiPart | undefined> {
    if (!reference) {
      return undefined;
    }

    if (reference.kind === 'dataUrl') {
      const mimeType = mimeFromDataUrl(reference.dataUrl) ?? 'image/png';
      return {
        inlineData: {
          mimeType,
          data: dataUrlToBase64(reference.dataUrl),
        },
      };
    }

    const response = await this.fetchImpl(reference.url, { signal });
    if (!response.ok) {
      throw new Error(`Failed to fetch reference image: ${response.status} ${response.statusText}`);
    }
    const bytes = Buffer.from(await response.arrayBuffer());
    if (bytes.length === 0) {
      throw new Error('Reference image URL returned an empty body');
    }
    const mimeType =
      detectImageType(bytes) ??
      response.headers.get('content-type')?.split(';')[0]?.trim() ??
      'image/png';
    return {
      inlineData: {
        mimeType,
        data: bytes.toString('base64'),
      },
    };
  }
}

function mimeFromDataUrl(dataUrl: string): string | undefined {
  const match = /^data:([^;,]+)/i.exec(dataUrl);
  return match?.[1];
}

function findInlineImagePart(
  payload: GeminiGenerateResponse | null,
): { mimeType?: string; data: string } | undefined {
  const parts = payload?.candidates?.[0]?.content?.parts ?? [];
  for (const part of parts) {
    const inline = part.inlineData ?? part.inline_data;
    if (inline?.data) {
      return {
        mimeType: inline.mimeType ?? inline.mime_type,
        data: inline.data,
      };
    }
  }
  return undefined;
}

function describeGeminiError(payload: GeminiGenerateResponse | null): string {
  if (!payload) {
    return 'no details';
  }
  if (typeof payload.error?.message === 'string' && payload.error.message.trim()) {
    return payload.error.message.trim().slice(0, 500);
  }
  return JSON.stringify(payload).slice(0, 500);
}
