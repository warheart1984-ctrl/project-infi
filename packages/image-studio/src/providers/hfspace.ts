import { detectImageType } from '../detectImageType.js';
import { dataUrlToBase64 } from './reference.js';
import type { ImageGenRequest, ImageGenResult, ImageProvider, ReferenceImage } from './types.js';

export const HF_SPACE_BASE_URL = 'https://m3st3rj4k3l-flux-2-klein-multi-lora.hf.space';
const HF_SPACE_MODEL = 'FLUX.2-Klein-9B';

const INFER_TIMEOUT_MS = 180_000;
const INFER_POLL_INTERVAL_MS = 4_000;
const CANVAS_MIN = 512;
const CANVAS_MAX = 2048;
const LORA_WEIGHTS = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0];

export interface HfSpaceConfig {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
}

type SpaceImageInput = { url: string } | { path: string };

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      'abort',
      () => {
        clearTimeout(timer);
        reject(signal.reason instanceof Error ? signal.reason : new Error('Aborted'));
      },
      { once: true },
    );
  });
}

interface SseEvent {
  name: string;
  data: string;
}

function parseSse(text: string): SseEvent[] {
  const events: SseEvent[] = [];
  let name = '';
  let payload: string[] = [];
  const push = (): void => {
    if (payload.length > 0) {
      events.push({ name, data: payload.join('\n') });
    }
    name = '';
    payload = [];
  };
  for (const line of text.split(/\r?\n/)) {
    if (line === '') {
      push();
      continue;
    }
    if (line.startsWith('event:')) {
      name = line.slice('event:'.length).trim();
      continue;
    }
    if (line.startsWith('data:')) {
      payload.push(line.slice('data:'.length).trimStart());
      continue;
    }
  }
  push();
  return events;
}

function extractImageUrl(sse: string): string | undefined {
  const match = sse.match(/"url"\s*:\s*"(https?:\/\/[^"]*gradio_api\/file=[^"]+)"/);
  return match?.[1]?.replace(/\\\//g, '/');
}

/**
 * Keyless provider for the community Hugging Face ZeroGPU Space
 * (FLUX.2-Klein-9B img2img). Talks to the Space's public Gradio API:
 * upload the base image, start an /infer event, poll for the result URL,
 * then download the generated PNG. Free but rate-limited and best-effort —
 * the Space is hosted by a third party and may be offline or change.
 */
export class HfSpaceProvider implements ImageProvider {
  readonly name = 'hfspace';
  readonly requiresApiKey = false;
  readonly configured = true;
  readonly configHelp =
    'Community Hugging Face ZeroGPU Space (FLUX.2-Klein-9B) — keyless but rate-limited; the Space may go offline or change.';

  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  constructor(config: HfSpaceConfig = {}) {
    this.baseUrl = (config.baseUrl ?? HF_SPACE_BASE_URL).replace(/\/+$/, '');
    this.fetchImpl = config.fetchImpl ?? fetch;
  }

  listModels(): Promise<string[]> {
    return Promise.resolve([HF_SPACE_MODEL]);
  }

  async generate(
    request: ImageGenRequest,
    options?: { signal?: AbortSignal },
  ): Promise<ImageGenResult> {
    const prompt = request.prompt.trim();
    if (!prompt) {
      throw new Error('HF Space requires a non-empty prompt');
    }
    if (!request.referenceImage) {
      throw new Error('This provider requires a base image (local file or --url)');
    }

    const baseImage = await this.buildBaseImage(request.referenceImage, options?.signal);
    const seed = request.seed ?? 0;
    const canvasMode = request.width || request.height ? 'Custom' : 'Auto (from base image)';

    const data: unknown[] = [
      baseImage,
      [],
      prompt,
      '',
      '',
      [],
      seed,
      false,
      1.0,
      4,
      'None',
      canvasMode,
      request.width ? clamp(Math.round(request.width), CANVAS_MIN, CANVAS_MAX) : 1024,
      request.height ? clamp(Math.round(request.height), CANVAS_MIN, CANVAS_MAX) : 1024,
      'Stretch',
      '#000000',
      1,
      'Random seed each run',
      0.4,
      1.4,
      {},
      ...LORA_WEIGHTS,
    ];

    const eventId = await this.startInference(data, options?.signal);
    const imageUrl = await this.awaitResult(eventId, options?.signal);

    const response = await this.fetchImpl(imageUrl, { signal: options?.signal });
    if (!response.ok) {
      throw new Error(`HF Space failed to download result (${response.status} ${response.statusText})`);
    }
    const bytes = Buffer.from(await response.arrayBuffer());
    const contentType =
      detectImageType(bytes) ?? response.headers.get('content-type') ?? 'application/octet-stream';

    return {
      provider: this.name,
      model: HF_SPACE_MODEL,
      contentType,
      bytes,
    };
  }

  private async buildBaseImage(
    reference: ReferenceImage,
    signal?: AbortSignal,
  ): Promise<SpaceImageInput> {
    if (reference.kind === 'url') {
      return { url: reference.url };
    }
    const bytes = Buffer.from(dataUrlToBase64(reference.dataUrl), 'base64');
    const form = new FormData();
    form.append('files', new Blob([bytes], { type: 'application/octet-stream' }), 'input.png');
    const response = await this.fetchImpl(`${this.baseUrl}/gradio_api/upload`, {
      method: 'POST',
      body: form,
      signal,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      throw new Error(`HF Space upload failed (${response.status}): ${detail.slice(0, 300) || 'no details'}`);
    }
    const body = (await response.json().catch(() => null)) as unknown;
    const path = Array.isArray(body) ? body[0] : undefined;
    if (typeof path !== 'string' || path.length === 0) {
      throw new Error('HF Space upload returned an unexpected response');
    }
    return { path };
  }

  private async startInference(data: unknown[], signal?: AbortSignal): Promise<string> {
    const response = await this.fetchImpl(`${this.baseUrl}/gradio_api/call/infer`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ data }),
      signal,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      throw new Error(`HF Space inference start failed (${response.status}): ${detail.slice(0, 300) || 'no details'}`);
    }
    const body = (await response.json().catch(() => null)) as { event_id?: unknown } | null;
    if (!body || typeof body.event_id !== 'string') {
      throw new Error('HF Space inference start returned an unexpected response');
    }
    return body.event_id;
  }

  private async awaitResult(eventId: string, signal?: AbortSignal): Promise<string> {
    const deadline = Date.now() + INFER_TIMEOUT_MS;
    while (Date.now() < deadline) {
      const response = await this.fetchImpl(`${this.baseUrl}/gradio_api/call/infer/${eventId}`, {
        signal,
      });
      if (response.ok) {
        const text = await response.text();
        for (const event of parseSse(text)) {
          const url = extractImageUrl(event.data);
          if (url) {
            return url;
          }
          const payload = this.tryParseJson(event.data);
          const eventName = event.name || (payload?.event as string | undefined);
          if (eventName === 'error' || eventName === 'complete') {
            if (eventName === 'complete') {
              throw new Error('HF Space finished without producing an image');
            }
            const detail =
              typeof payload?.error === 'string'
                ? (payload.error as string)
                : typeof payload?.message === 'string'
                  ? (payload.message as string)
                  : 'unknown error';
            throw new Error(`HF Space inference failed: ${detail}`);
          }
        }
      }
      await sleep(INFER_POLL_INTERVAL_MS, signal);
    }
    throw new Error('HF Space generation timed out');
  }

  private tryParseJson(text: string): Record<string, unknown> | undefined {
    try {
      const parsed = JSON.parse(text) as unknown;
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>;
      }
    } catch {
      // not JSON — ignore
    }
    return undefined;
  }
}
