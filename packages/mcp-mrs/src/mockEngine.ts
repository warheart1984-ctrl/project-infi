import http from 'node:http';
import { randomUUID, createHash } from 'node:crypto';
import type { IncomingMessage, ServerResponse } from 'node:http';

interface SceneRecord {
  sceneId: string;
  sceneSpec: Record<string, unknown>;
  sceneSpecHash: string;
  createdAt: number;
}

interface RenderResult {
  renderId: string;
  sceneId: string;
  width: number;
  height: number;
  seed: number;
  trajectoryRoot: string;
  sceneSpecHash: string;
  projectionHash: string;
  pixelHash: string;
  pngHash: string;
  rendererVersion: string;
  runtimeFingerprint: {
    node: string;
    zlib: string;
    platform: string;
    arch: string;
  };
  evidenceStatus: 'substrate_verified';
  promotionStatus: 'not_promoted_to_ciems';
  pngBase64: string;
}

function sha256Hex(input: string): string {
  return createHash('sha256').update(input, 'utf-8').digest('hex');
}

function generateMinimalPngBase64(): string {
  const pngBytes = Buffer.from([
    0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
    0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4,
    0x89, 0x00, 0x00, 0x00, 0x0a, 0x49, 0x44, 0x41,
    0x54, 0x78, 0x9c, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0d, 0x0a, 0x2d, 0xb4, 0x00,
    0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, 0x44, 0xae,
    0x42, 0x60, 0x82,
  ]);
  return pngBytes.toString('base64');
}

const MINIMAL_PNG_BASE64 = generateMinimalPngBase64();

export class MockMrsEngine {
  private server: http.Server | null = null;
  private scenes: Map<string, SceneRecord> = new Map();
  private port: number;

  constructor(port = 8080) {
    this.port = port;
  }

  async start(): Promise<number> {
    return new Promise((resolve, reject) => {
      this.server = http.createServer((req, res) => this._handleRequest(req, res));
      this.server.listen(this.port, () => {
        const addr = this.server!.address();
        if (addr && typeof addr === 'object') {
          this.port = addr.port;
        }
        resolve(this.port);
      });
      this.server.on('error', reject);
    });
  }

  async stop(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.server) {
        resolve();
        return;
      }
      this.server.close((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  getBaseUrl(): string {
    return `http://127.0.0.1:${this.port}`;
  }

  private _handleRequest(req: IncomingMessage, res: ServerResponse): void {
    const url = new URL(req.url ?? '/', `http://localhost:${this.port}`);
    const method = req.method ?? 'GET';

    if (method === 'POST' && url.pathname === '/v1/scenes') {
      this._handleCreateScene(req, res);
    } else if (method === 'POST' && url.pathname.startsWith('/v1/scenes/') && url.pathname.endsWith('/render')) {
      this._handleRenderScene(req, res, url.pathname);
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
    }
  }

  private _handleCreateScene(req: IncomingMessage, res: ServerResponse): void {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      try {
        const parsed = JSON.parse(body);
        const sceneId = `scene-${randomUUID().slice(0, 16)}`;
        const sceneSpecHash = sha256Hex(JSON.stringify(parsed.sceneSpec ?? {}));

        this.scenes.set(sceneId, {
          sceneId,
          sceneSpec: parsed.sceneSpec ?? {},
          sceneSpecHash,
          createdAt: Date.now(),
        });

        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ sceneId, sceneSpecHash }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
  }

  private _handleRenderScene(req: IncomingMessage, res: ServerResponse, pathname: string): void {
    const sceneId = pathname.split('/')[3];
    const scene = this.scenes.get(sceneId);

    if (!scene) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Scene not found' }));
      return;
    }

    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
        const renderId = `rt4d-render-${randomUUID().replace(/-/g, '').slice(0, 16)}`;
      const projectionHash = sha256Hex(`projection:${scene.sceneSpecHash}:${scene.sceneId}`);
      const pixelHash = sha256Hex(`pixel:${projectionHash}:${renderId}`);
      const pngHash = sha256Hex(MINIMAL_PNG_BASE64);

      const result: RenderResult = {
        renderId,
        sceneId: scene.sceneId,
        width: 1024,
        height: 1024,
        seed: 42,
        trajectoryRoot: `/trajectories/${scene.sceneId}`,
        sceneSpecHash: scene.sceneSpecHash,
        projectionHash,
        pixelHash,
        pngHash,
        rendererVersion: '1.0.0',
        runtimeFingerprint: {
          node: process.version,
          zlib: '1.3.1',
          platform: process.platform,
          arch: process.arch,
        },
        evidenceStatus: 'substrate_verified',
        promotionStatus: 'not_promoted_to_ciems',
        pngBase64: MINIMAL_PNG_BASE64,
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    });
  }
}