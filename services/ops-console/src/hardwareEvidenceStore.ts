import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

import type { HardwareBenchmarkRunArtifact, HardwareReplayArtifact } from './hardwareConsole.js';

export type HardwareEvidenceKind = 'benchmark' | 'replay';

export interface HardwareEvidenceRecord {
  id: string;
  kind: HardwareEvidenceKind;
  title: string;
  source: string;
  recordedAt: string;
  payload: HardwareBenchmarkRunArtifact | HardwareReplayArtifact;
}

export interface HardwareEvidenceSummary {
  available: boolean;
  storePath: string;
  entryCount: number;
  benchmarkCount: number;
  replayCount: number;
  latestBenchmark: HardwareEvidenceRecord | null;
  latestReplay: HardwareEvidenceRecord | null;
  recentRecords: HardwareEvidenceRecord[];
}

export interface HardwareEvidenceStoreOptions {
  filePath?: string;
  env?: NodeJS.ProcessEnv;
}

export class HardwareEvidenceStore {
  private readonly env: NodeJS.ProcessEnv;
  private readonly filePath?: string;

  constructor(options: HardwareEvidenceStoreOptions = {}) {
    this.env = options.env ?? process.env;
    this.filePath = options.filePath;
  }

  appendBenchmark(
    payload: HardwareBenchmarkRunArtifact,
    metadata: { title?: string; source?: string; id?: string; recordedAt?: string } = {},
  ): HardwareEvidenceRecord {
    return this.append({
      kind: 'benchmark',
      title: metadata.title ?? 'Hardware Benchmark Run',
      source: metadata.source ?? 'ops-console',
      id: metadata.id,
      recordedAt: metadata.recordedAt,
      payload,
    });
  }

  appendReplay(
    payload: HardwareReplayArtifact,
    metadata: { title?: string; source?: string; id?: string; recordedAt?: string } = {},
  ): HardwareEvidenceRecord {
    return this.append({
      kind: 'replay',
      title: metadata.title ?? 'Hardware Replay Comparison',
      source: metadata.source ?? 'ops-console',
      id: metadata.id,
      recordedAt: metadata.recordedAt,
      payload,
    });
  }

  append(
    record: Omit<HardwareEvidenceRecord, 'id' | 'recordedAt'> & { id?: string; recordedAt?: string },
  ): HardwareEvidenceRecord {
    const storePath = this.resolveStorePath();
    ensureParentDirectory(storePath);
    const records = this.list(storePath);
    const nextRecord: HardwareEvidenceRecord = {
      id: record.id?.trim() || `hw-${record.kind}-${(records.length + 1).toString(36)}`,
      kind: record.kind,
      title: record.title,
      source: record.source,
      recordedAt: record.recordedAt ?? new Date().toISOString(),
      payload: record.payload,
    };
    appendFileSync(storePath, `${JSON.stringify(nextRecord)}\n`, 'utf8');
    return nextRecord;
  }

  list(storePath = this.resolveStorePath()): HardwareEvidenceRecord[] {
    if (!existsSync(storePath)) {
      return [];
    }

    const content = readFileSync(storePath, 'utf8');
    return content
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => JSON.parse(line) as HardwareEvidenceRecord);
  }

  summary(): HardwareEvidenceSummary {
    const storePath = this.resolveStorePath();
    const records = this.list(storePath);
    const benchmarkRecords = records.filter((record) => record.kind === 'benchmark');
    const replayRecords = records.filter((record) => record.kind === 'replay');

    return {
      available: records.length > 0,
      storePath,
      entryCount: records.length,
      benchmarkCount: benchmarkRecords.length,
      replayCount: replayRecords.length,
      latestBenchmark: benchmarkRecords.at(-1) ?? null,
      latestReplay: replayRecords.at(-1) ?? null,
      recentRecords: records.slice(-10).reverse(),
    };
  }

  private resolveStorePath(): string {
    if (this.filePath?.trim()) {
      return path.resolve(this.filePath.trim());
    }

    const envPath = this.env.SOVEREIGNX_HARDWARE_EVIDENCE_STORE?.trim();
    if (envPath) {
      return path.resolve(envPath);
    }

    return path.resolve(process.cwd(), '.runtime', 'hardware-evidence.jsonl');
  }
}

export function createHardwareEvidenceStore(options: HardwareEvidenceStoreOptions = {}): HardwareEvidenceStore {
  return new HardwareEvidenceStore(options);
}

function ensureParentDirectory(storePath: string): void {
  mkdirSync(path.dirname(storePath), { recursive: true });
}
