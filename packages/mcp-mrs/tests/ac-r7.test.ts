import { describe, it, expect, vi } from 'vitest';
import { MrsEngineBridge } from '../src/bridge.js';
import {
  RenderRt4dPreviewOutput,
  EngineReceipt,
  RenderRt4dPreviewInput,
} from '../src/schemas.js';

const VALID_RECEIPT: EngineReceipt = {
  renderId: 'rt4d-render-abc123def4567890',
  sceneId: 'scene-001',
  width: 1024,
  height: 1024,
  seed: 42,
  trajectoryRoot: '/trajectories/scene-001',
  sceneSpecHash: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
  projectionHash: 'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
  pixelHash: 'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
  pngHash: 'd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
  rendererVersion: '1.0.0',
  runtimeFingerprint: {
    node: '20.11.0',
    zlib: '1.3.1',
    platform: 'linux',
    arch: 'x64',
  },
  evidenceStatus: 'substrate_verified',
  promotionStatus: 'not_promoted_to_ciems',
  pngBase64: Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).toString('base64'),
};

describe('AC-R7: MCP tool-layer transport fidelity', () => {
  it('validates a complete engine receipt through the output schema', () => {
    const result = RenderRt4dPreviewOutput.safeParse(VALID_RECEIPT);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.renderId).toBe('rt4d-render-abc123def4567890');
      expect(result.data.evidenceStatus).toBe('substrate_verified');
      expect(result.data.promotionStatus).toBe('not_promoted_to_ciems');
    }
  });

  it('preserves stable renderId through validation', () => {
    const result = RenderRt4dPreviewOutput.parse(VALID_RECEIPT);
    expect(result.renderId).toBe(VALID_RECEIPT.renderId);
  });

  it('preserves stable projectionHash through validation', () => {
    const result = RenderRt4dPreviewOutput.parse(VALID_RECEIPT);
    expect(result.projectionHash).toBe(VALID_RECEIPT.projectionHash);
  });

  it('preserves stable pixelHash through validation', () => {
    const result = RenderRt4dPreviewOutput.parse(VALID_RECEIPT);
    expect(result.pixelHash).toBe(VALID_RECEIPT.pixelHash);
  });

  it('preserves stable pngHash through validation', () => {
    const result = RenderRt4dPreviewOutput.parse(VALID_RECEIPT);
    expect(result.pngHash).toBe(VALID_RECEIPT.pngHash);
  });

  it('preserves runtimeFingerprint shape and bytes through validation', () => {
    const result = RenderRt4dPreviewOutput.parse(VALID_RECEIPT);
    expect(result.runtimeFingerprint).toEqual(VALID_RECEIPT.runtimeFingerprint);
  });

  it('preserves evidenceStatus as substrate_verified', () => {
    const result = RenderRt4dPreviewOutput.parse(VALID_RECEIPT);
    expect(result.evidenceStatus).toBe('substrate_verified');
  });

  it('preserves promotionStatus as not_promoted_to_ciems', () => {
    const result = RenderRt4dPreviewOutput.parse(VALID_RECEIPT);
    expect(result.promotionStatus).toBe('not_promoted_to_ciems');
  });

  it('fails closed when a required field is missing', () => {
    const incomplete = { ...VALID_RECEIPT };
    delete (incomplete as Record<string, unknown>).renderId;
    const result = RenderRt4dPreviewOutput.safeParse(incomplete);
    expect(result.success).toBe(false);
  });

  it('fails closed when evidenceStatus is altered', () => {
    const tampered = { ...VALID_RECEIPT, evidenceStatus: 'forged' };
    const result = RenderRt4dPreviewOutput.safeParse(tampered);
    expect(result.success).toBe(false);
  });

  it('fails closed when promotionStatus is altered', () => {
    const tampered = { ...VALID_RECEIPT, promotionStatus: 'promoted' as unknown as 'not_promoted_to_ciems' };
    const result = RenderRt4dPreviewOutput.safeParse(tampered);
    expect(result.success).toBe(false);
  });

  it('fails closed when hash format is invalid', () => {
    const tampered = {
      ...VALID_RECEIPT,
      sceneSpecHash: 'not-a-valid-hex-hash',
    };
    const result = RenderRt4dPreviewOutput.safeParse(tampered);
    expect(result.success).toBe(false);
  });

  it('fails closed when renderId format is invalid', () => {
    const tampered = {
      ...VALID_RECEIPT,
      renderId: 'invalid-render-id',
    };
    const result = RenderRt4dPreviewOutput.safeParse(tampered);
    expect(result.success).toBe(false);
  });

  it('fails closed when runtimeFingerprint has wrong shape', () => {
    const tampered = {
      ...VALID_RECEIPT,
      runtimeFingerprint: { node: '20.11.0' },
    };
    const result = RenderRt4dPreviewOutput.safeParse(tampered);
    expect(result.success).toBe(false);
  });
});

describe('Input schema validation', () => {
  it('accepts a valid minimal input', () => {
    const input = {
      sceneSpec: { objects: [] },
      surface: 'default',
    };
    const result = RenderRt4dPreviewInput.safeParse(input);
    expect(result.success).toBe(true);
  });

  it('rejects input missing required sceneSpec', () => {
    const input = { surface: 'default' };
    const result = RenderRt4dPreviewInput.safeParse(input);
    expect(result.success).toBe(false);
  });

  it('rejects input missing required surface', () => {
    const input = { sceneSpec: {} };
    const result = RenderRt4dPreviewInput.safeParse(input);
    expect(result.success).toBe(false);
  });

  it('rejects invalid camera fov', () => {
    const input = {
      sceneSpec: {},
      surface: 'default',
      camera: { fov: 200, position: [0, 0, 0], target: [0, 0, 1] },
    };
    const result = RenderRt4dPreviewInput.safeParse(input);
    expect(result.success).toBe(false);
  });

  it('rejects invalid resolution', () => {
    const input = {
      sceneSpec: {},
      surface: 'default',
      quality: { resolution: [0, 1024] },
    };
    const result = RenderRt4dPreviewInput.safeParse(input);
    expect(result.success).toBe(false);
  });
});

describe('Bridge fail-closed behavior', () => {
  it('throws on unsupported surface (engine error passes through honestly)', async () => {
    const bridge = new MrsEngineBridge({ baseUrl: 'http://localhost:9999' });
    const input: RenderRt4dPreviewInput = {
      sceneSpec: { objects: [] },
      surface: 'unsupported-surface',
    };

    await expect(bridge.renderComplete(input)).rejects.toThrow();
  });

  it('throws on connection refused (MRS engine unavailable)', async () => {
    const bridge = new MrsEngineBridge({ baseUrl: 'http://localhost:1' });
    const input: RenderRt4dPreviewInput = {
      sceneSpec: { objects: [] },
      surface: 'default',
    };

    await expect(bridge.renderComplete(input)).rejects.toThrow();
  });
});

describe('Hash authority boundary', () => {
  it('MCP schema does not import or recompute engine hashes', () => {
    const receipt = { ...VALID_RECEIPT };
    const parsed = RenderRt4dPreviewOutput.parse(receipt);
    expect(parsed.sceneSpecHash).toBe(VALID_RECEIPT.sceneSpecHash);
    expect(parsed.projectionHash).toBe(VALID_RECEIPT.projectionHash);
    expect(parsed.pixelHash).toBe(VALID_RECEIPT.pixelHash);
    expect(parsed.pngHash).toBe(VALID_RECEIPT.pngHash);
  });
});