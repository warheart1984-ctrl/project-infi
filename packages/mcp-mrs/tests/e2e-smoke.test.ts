import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { MockMrsEngine } from '../src/mockEngine.js';
import { EvidenceStore } from '../src/evidenceStore.js';
import { MrsEngineBridge } from '../src/bridge.js';
import { RenderRt4dPreviewInput, RenderRt4dPreviewOutput } from '../src/schemas.js';
import { existsSync, mkdirSync, rmSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { randomUUID } from 'node:crypto';
import { createHash } from 'node:crypto';

const VALID_INPUT: RenderRt4dPreviewInput = {
  sceneSpec: {
    objects: [
      {
        type: 'sphere',
        position: [0, 0, 0],
        radius: 1,
        material: { color: '#ff0000', roughness: 0.5 },
      },
    ],
    lighting: {
      ambient: 0.2,
      sun: { direction: [0, 1, 0], intensity: 1.0, color: '#ffffff' },
    },
  },
  surface: 'default',
  seed: 42,
  camera: {
    fov: 60,
    position: [0, 2, 5],
    target: [0, 0, 0],
    rotations: [0, 0, 0],
  },
  quality: {
    resolution: [1024, 1024],
    spp: 64,
    maxDepth: 5,
  },
  trajectory: [
    [0, 0, 5],
    [1, 0, 5],
    [1, 1, 5],
    [0, 1, 5],
    [0, 0, 5],
  ],
};

function sha256Hex(input: string): string {
  return createHash('sha256').update(input, 'utf-8').digest('hex');
}

describe('E2E constitutional smoke test', () => {
  let engine: MockMrsEngine;
  let enginePort: number;
  let evidenceDir: string;
  let store: EvidenceStore;
  let bridge: MrsEngineBridge;

  beforeAll(async () => {
    engine = new MockMrsEngine(0);
    enginePort = await engine.start();

    evidenceDir = join(tmpdir(), `mcp-mrs-e2e-${randomUUID()}`);
    if (!existsSync(evidenceDir)) {
      mkdirSync(evidenceDir, { recursive: true });
    }
    store = new EvidenceStore(evidenceDir);
    bridge = new MrsEngineBridge({ baseUrl: engine.getBaseUrl(), timeoutMs: 120000 });
  });

  afterAll(async () => {
    await engine.stop();
    rmSync(evidenceDir, { recursive: true, force: true });
  });

  it('bridge calls mock engine and returns a valid receipt with stable hashes', async () => {
    const receipt = await bridge.renderComplete(VALID_INPUT);

    const parseResult = RenderRt4dPreviewOutput.safeParse(receipt);
    expect(parseResult.success).toBe(true);
    if (!parseResult.success) return;

    const validated = parseResult.data;
    expect(validated.renderId).toMatch(/^rt4d-render-[a-f0-9]{16}$/);
    expect(validated.sceneId).toBeTruthy();
    expect(validated.width).toBe(1024);
    expect(validated.height).toBe(1024);
    expect(validated.seed).toBe(42);
    expect(validated.evidenceStatus).toBe('substrate_verified');
    expect(validated.promotionStatus).toBe('not_promoted_to_ciems');
    expect(validated.pngBase64).toBeTruthy();

    const pngBytes = Buffer.from(validated.pngBase64, 'base64');
    expect(pngBytes[0]).toBe(0x89);
    expect(pngBytes[1]).toBe(0x50);
    expect(pngBytes[2]).toBe(0x4e);
    expect(pngBytes[3]).toBe(0x47);

    const actualPngHash = sha256Hex(validated.pngBase64);
    expect(actualPngHash).toBe(validated.pngHash);

    const actualSceneSpecHash = sha256Hex(JSON.stringify(VALID_INPUT.sceneSpec));
    expect(receipt.sceneSpecHash).toBe(actualSceneSpecHash);
  });

  it('bridge enforces scene spec hash consistency between create and render steps', async () => {
    const { sceneId, sceneSpecHash } = await bridge.createScene(VALID_INPUT);
    const receipt = await bridge.renderScene(sceneId);

    expect(receipt.sceneSpecHash).toBe(sceneSpecHash);
  });

  it('evidence store saves, loads, and replays receipts with matching hash identities', async () => {
    const receipt = await bridge.renderComplete(VALID_INPUT);
    const validated = RenderRt4dPreviewOutput.parse(receipt);

    const saved = store.save(validated);
    expect(saved.replayToken).toBeTruthy();
    expect(saved.renderId).toBe(validated.renderId);
    expect(saved.sceneSpecHash).toBe(validated.sceneSpecHash);
    expect(saved.projectionHash).toBe(validated.projectionHash);
    expect(saved.pixelHash).toBe(validated.pixelHash);
    expect(saved.pngHash).toBe(validated.pngHash);

    const loaded = store.load(validated.renderId);
    expect(loaded).not.toBeNull();
    expect(loaded!.renderId).toBe(validated.renderId);
    expect(loaded!.sceneSpecHash).toBe(validated.sceneSpecHash);
    expect(loaded!.projectionHash).toBe(validated.projectionHash);
    expect(loaded!.pixelHash).toBe(validated.pixelHash);
    expect(loaded!.pngHash).toBe(validated.pngHash);

    const replayed = store.replay(saved.replayToken);
    expect(replayed).not.toBeNull();
    expect(replayed!.renderId).toBe(validated.renderId);
    expect(replayed!.sceneSpecHash).toBe(validated.sceneSpecHash);
    expect(replayed!.projectionHash).toBe(validated.projectionHash);
    expect(replayed!.pixelHash).toBe(validated.pixelHash);
    expect(replayed!.pngHash).toBe(validated.pngHash);
  });

  it('evidence store persists receipts to disk and file contents match in-memory', async () => {
    const receipt = await bridge.renderComplete(VALID_INPUT);
    const validated = RenderRt4dPreviewOutput.parse(receipt);

    const saved = store.save(validated);
    const evidenceFile = join(evidenceDir, `${validated.renderId}.json`);
    expect(existsSync(evidenceFile)).toBe(true);

    const fileContent = JSON.parse(readFileSync(evidenceFile, 'utf-8'));
    expect(fileContent.renderId).toBe(validated.renderId);
    expect(fileContent.sceneSpecHash).toBe(validated.sceneSpecHash);
    expect(fileContent.projectionHash).toBe(validated.projectionHash);
    expect(fileContent.pixelHash).toBe(validated.pixelHash);
    expect(fileContent.pngHash).toBe(validated.pngHash);
    expect(fileContent.replayToken).toBe(saved.replayToken);
    expect(fileContent.evidenceStatus).toBe('substrate_verified');
    expect(fileContent.promotionStatus).toBe('not_promoted_to_ciems');
  });

  it('full chain: render → save → load → replay preserves all hash identities', async () => {
    const receipt = await bridge.renderComplete(VALID_INPUT);
    const validated = RenderRt4dPreviewOutput.parse(receipt);

    const saved = store.save(validated);
    const loaded = store.load(validated.renderId)!;
    const replayed = store.replay(saved.replayToken)!;

    const hashes = ['sceneSpecHash', 'projectionHash', 'pixelHash', 'pngHash'] as const;
    for (const hash of hashes) {
      expect(loaded[hash]).toBe(validated[hash]);
      expect(replayed[hash]).toBe(validated[hash]);
      expect(saved[hash]).toBe(validated[hash]);
    }
  });

  it('fail-closed: evidence store returns null for missing renderId', () => {
    const result = store.load('nonexistent-render-id');
    expect(result).toBeNull();
  });

  it('fail-closed: evidence store returns null for missing replayToken', () => {
    const result = store.replay('nonexistent-token');
    expect(result).toBeNull();
  });
});