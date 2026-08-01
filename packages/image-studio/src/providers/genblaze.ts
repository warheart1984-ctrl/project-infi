import { detectImageType } from '../detectImageType.js';
import type { ImageGenRequest, ImageGenResult, ImageProvider, ProviderEnv } from './types.js';

export interface GenblazeConfig {
  baseUrl?: string;
  apiKey?: string;
  env?: ProviderEnv;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}

const DEFAULT_BASE_URL = 'http://127.0.0.1:8787';
const DEFAULT_TIMEOUT_MS = 120_000;

export class GenblazeProvider implements ImageProvider {
  readonly name = 'genblaze';
  readonly requiresApiKey = true;
  readonly configHelp =
    'Genblaze media server (MRS stills via StoryForge boundary). Start: `pnpm --filter genblaze-media start` at G:\\Mandala Rendering Software. Required: set GENBLAZE_API_KEY (Bearer token) or GENBLAZE_BASE_URL to your local Genblaze server.';

  private readonly baseUrl: string;
  private readonly apiKey: string | undefined;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;

  constructor(config: GenblazeConfig = {}) {
    const env = config.env ?? process.env;
    this.baseUrl = (config.baseUrl ?? env.GENBLAZE_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/+$/, '');
    this.apiKey = config.apiKey ?? env.GENBLAZE_API_KEY;
    this.fetchImpl = config.fetchImpl ?? fetch;
    this.timeoutMs = config.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  }

  get configured(): boolean {
    return true;
  }

  listModels(): Promise<string[]> {
    return Promise.resolve([
      'mrs-scene-spec',
      'mrs-engine3d-still',
      'mrs-proton-raster',
      'mrs-rt4d',
    ]);
  }

  async generate(
    request: ImageGenRequest,
    options?: { signal?: AbortSignal },
  ): Promise<ImageGenResult> {
    const prompt = request.prompt.trim();
    if (!prompt) {
      throw new Error('Genblaze provider requires a non-empty prompt');
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);
    options?.signal?.addEventListener('abort', () => controller.abort());

    try {
      const renderRequest = this.buildRenderRequest(request, prompt);
      
      const headers: Record<string, string> = {
        'content-type': 'application/json',
      };
      if (this.apiKey) {
        headers['authorization'] = `Bearer ${this.apiKey}`;
      }

      const response = await this.fetchImpl(`${this.baseUrl}/api/render-request`, {
        method: 'POST',
        headers,
        body: JSON.stringify(renderRequest),
        signal: controller.signal,
      });

      if (!response.ok) {
        const detail = await response.text().catch(() => '');
        throw new Error(`Genblaze render-request failed (${response.status}): ${detail.slice(0, 500) || 'no details'}`);
      }

      const result = (await response.json()) as GenblazeRenderResult;
      
      const previewUrl = this.resolvePreviewUrl(result.artifacts[0]);
      
      const imageResponse = await this.fetchImpl(previewUrl, { signal: controller.signal });
      if (!imageResponse.ok) {
        throw new Error(`Failed to download artifact (${imageResponse.status})`);
      }
      const bytes = Buffer.from(await imageResponse.arrayBuffer());
      const contentType = detectImageType(bytes) ?? 'image/png';

      return {
        provider: this.name,
        model: request.model ?? 'mrs-scene-spec',
        contentType,
        bytes,
      };
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private buildRenderRequest(request: ImageGenRequest, prompt: string): RenderRequestInput {
    const requestId = `run-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
    const width = request.width ?? 512;
    const height = request.height ?? 512;
    const seed = request.seed ?? 42;
    
    const route = this.inferRoute(request.model);
    
    const render: RenderInput = {
      width,
      height,
      samples: request.model?.includes('cinematic') ? 24 : 4,
      maxDepth: 4,
      seed,
      quality: request.model?.includes('cinematic') ? 'cinematic' : request.model?.includes('hq') ? 'high' : 'draft',
    };

    let sceneSpecification: SceneSpecInput | undefined;
    if (route === 'scene-spec' || route === 'rt4d') {
      sceneSpecification = this.promptToSceneSpec(prompt, width, height, seed);
    }

    return {
      schemaVersion: '1.0',
      requestId,
      intentId: `intent-${requestId}`,
      worldId: `world-${requestId}`,
      timelineId: `timeline-${requestId}`,
      timeSeconds: 0,
      parameters: { purpose: 'aais-genblaze-provider' },
      provenance: {},
      payload: {
        route,
        render,
        ...(sceneSpecification && { sceneSpecification }),
      },
    };
  }

  private inferRoute(model?: string): RenderRoute {
    if (!model) return 'scene-spec';
    const m = model.toLowerCase();
    if (m.includes('engine3d')) return 'engine3d-world';
    if (m.includes('proton')) return 'proton-raster';
    if (m.includes('rt4d')) return 'rt4d';
    return 'scene-spec';
  }

  private promptToSceneSpec(prompt: string, width: number, height: number, seed: number): SceneSpecInput {
    return {
      schemaVersion: '1.0',
      kind: 'SceneSpecification',
      id: `prompt-scene-${Date.now()}`,
      name: `From prompt: ${prompt.slice(0, 60)}`,
      materials: [
        {
          id: 'mat1',
          color: '#88aaff',
          opacity: 1,
        },
      ],
      entities: [
        {
          id: 'ent1',
          materialId: 'mat1',
          geometry: {
            kind: 'surface',
            surfaceId: 'tesseract',
          },
        },
      ],
      camera: {
        position4d: [4.3, 1.4, 0.2, 0.1],
        target4d: [0, 0.1, 0, 0],
        fovX: 52,
        fovY: 52,
        fovZ: 45,
        fovW: 28,
      },
      lights: [
        {
          id: 'key',
          center: [2.4, 3.3, -1.6, 0.7],
          radius: 0.95,
          emission: [17, 16, 14.5],
        },
      ],
      output: { width, height, samples: 2, maxDepth: 2, seed },
    };
  }

  private resolvePreviewUrl(artifact: { uri: string; requestId?: string }): string {
    const path = artifact.uri;
    if (path.startsWith('http')) return path;
    
    const outputMatch = path.match(/output\/(.+?)-scene-spec\.png$/);
    if (outputMatch) {
      return `${this.baseUrl}/api/preview/${outputMatch[1]}`;
    }
    
    const uuidMatch = path.match(/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
    if (uuidMatch) {
      return `${this.baseUrl}/api/preview/${uuidMatch[1]}`;
    }
    
    const timestampMatch = path.match(/run-([0-9a-f]+)/);
    if (timestampMatch) {
      return `${this.baseUrl}/api/preview/${timestampMatch[1]}`;
    }
    
    const runsMatch = path.match(/runs\/([^/]+)/);
    if (runsMatch) {
      return `${this.baseUrl}/api/preview/${runsMatch[1]}`;
    }
    
    if (artifact.requestId) {
      return `${this.baseUrl}/api/preview/${artifact.requestId}`;
    }
    
    throw new Error(`Could not extract run_id from artifact URI: ${path}`);
  }
}

interface RenderRequestInput {
  schemaVersion: string;
  requestId: string;
  intentId: string;
  worldId: string;
  timelineId: string;
  timeSeconds: number;
  parameters: Record<string, string>;
  provenance: Record<string, unknown>;
  payload: {
    route: RenderRoute;
    render: RenderInput;
    sceneSpecification?: SceneSpecInput;
  };
}

type RenderRoute = 'scene-spec' | 'engine3d-world' | 'proton-raster' | 'rt4d';

interface RenderInput {
  width: number;
  height: number;
  samples: number;
  maxDepth: number;
  seed: number;
  quality: 'draft' | 'high' | 'cinematic';
}

interface SceneSpecInput {
  schemaVersion: string;
  kind: string;
  id: string;
  name: string;
  materials: Array<{ id: string; color: string; opacity: number }>;
  entities: Array<{ id: string; materialId: string; geometry: { kind: string; surfaceId: string } }>;
  camera: { position4d: number[]; target4d: number[]; fovX: number; fovY: number; fovZ: number; fovW: number };
  lights: Array<{ id: string; center: number[]; radius: number; emission: number[] }>;
  output: { width: number; height: number; samples: number; maxDepth: number; seed: number };
}

interface GenblazeRenderResult {
  schemaVersion: string;
  requestId: string;
  status: 'ok' | 'error' | 'refused';
  provenance: Record<string, unknown>;
  routeUsed: string;
  artifacts: Array<{
    role: string;
    uri: string;
    sha256: string;
    mediaType: string;
  }>;
  mapping: Record<string, unknown>;
  error?: { code: string; message: string };
  sceneSpecification?: SceneSpecInput;
}