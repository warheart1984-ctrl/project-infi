import { z } from 'zod';
import { RenderRt4dPreviewInput, EngineReceiptSchema, type EngineReceipt } from './schemas.js';

export interface MrsEngineConfig {
  baseUrl: string;
  apiKey?: string;
  timeoutMs?: number;
}

export class MrsEngineBridge {
  private readonly config: MrsEngineConfig;

  constructor(config: MrsEngineConfig) {
    this.config = config;
  }

  async createScene(input: RenderRt4dPreviewInput): Promise<{ sceneId: string; sceneSpecHash: string }> {
    const url = `${this.config.baseUrl}/v1/scenes`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        sceneSpec: input.sceneSpec,
        surface: input.surface,
        seed: input.seed,
        camera: input.camera,
        quality: input.quality,
        trajectory: input.trajectory,
      }),
      signal: AbortSignal.timeout(this.config.timeoutMs ?? 30000),
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`MRS scene creation failed (${res.status}): ${detail}`);
    }

    const json = (await res.json()) as { sceneId: string; sceneSpecHash: string };
    return json;
  }

  async renderScene(sceneId: string): Promise<EngineReceipt> {
    const url = `${this.config.baseUrl}/v1/scenes/${sceneId}/render`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    const res = await fetch(url, {
      method: 'POST',
      headers,
      signal: AbortSignal.timeout(this.config.timeoutMs ?? 120000),
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`MRS render failed (${res.status}): ${detail}`);
    }

    const json = (await res.json()) as EngineReceipt;
    return json;
  }

  async renderComplete(input: RenderRt4dPreviewInput): Promise<EngineReceipt> {
    const { sceneId, sceneSpecHash } = await this.createScene(input);
    const receipt = await this.renderScene(sceneId);

    if (receipt.sceneSpecHash !== sceneSpecHash) {
      throw new Error('Scene spec hash mismatch between create and render steps');
    }

    return receipt;
  }
}