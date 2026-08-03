import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { RenderRt4dPreviewOutput, type EngineReceipt } from './schemas.js';

export interface EvidenceReceipt {
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
  pngBase64?: string;
  createdAt: number;
  replayToken: string;
}

export class EvidenceStore {
  private baseDir: string;

  constructor(baseDir: string) {
    this.baseDir = baseDir;
    if (!existsSync(baseDir)) {
      mkdirSync(baseDir, { recursive: true });
    }
  }

  save(receipt: EngineReceipt): EvidenceReceipt {
    const replayToken = randomHex(32);
    const evidence: EvidenceReceipt = {
      ...receipt,
      createdAt: Date.now(),
      replayToken,
    };

    const filePath = join(this.baseDir, `${receipt.renderId}.json`);
    writeFileSync(filePath, JSON.stringify(evidence, null, 2));

    return evidence;
  }

  load(renderId: string): EvidenceReceipt | null {
    const filePath = join(this.baseDir, `${renderId}.json`);
    if (!existsSync(filePath)) return null;
    const raw = readFileSync(filePath, 'utf-8');
    return JSON.parse(raw) as EvidenceReceipt;
  }

  replay(replayToken: string): EvidenceReceipt | null {
    const renderIds = this._listRenderIds();
    for (const id of renderIds) {
      const receipt = this.load(id);
      if (receipt && receipt.replayToken === replayToken) {
        return receipt;
      }
    }
    return null;
  }

  listAll(): EvidenceReceipt[] {
    return this._listRenderIds().map((id) => this.load(id)!);
  }

  private _listRenderIds(): string[] {
    if (!existsSync(this.baseDir)) return [];
    return readdirSync(this.baseDir)
      .filter((f) => f.endsWith('.json'))
      .map((f) => f.slice(0, -5));
  }
}

function randomHex(length: number): string {
  const bytes = new Uint8Array(length / 2);
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i++) {
      bytes[i] = Math.floor(Math.random() * 256);
    }
  }
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
