import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

import type { SovereignXHardwareSnapshot } from './SovereignXHardwareTelemetryAdapter.js';

export type SovereignXHardwareReplayRecord = {
  sequence: number;
  recordedAt: string;
  snapshot: SovereignXHardwareSnapshot;
};

export type SovereignXHardwareReplaySummary = {
  available: boolean;
  storePath: string;
  entryCount: number;
  latest: {
    sequence: number;
    recordedAt: string;
    source: SovereignXHardwareSnapshot['source'];
    sourceDetail: string;
    decision: SovereignXHardwareSnapshot['cycle']['decision'];
  } | null;
  recentRecords: {
    sequence: number;
    recordedAt: string;
    source: SovereignXHardwareSnapshot['source'];
    sourceDetail: string;
    decision: SovereignXHardwareSnapshot['cycle']['decision'];
  }[];
};

export interface SovereignXHardwareReplayStoreOptions {
  filePath?: string;
  env?: NodeJS.ProcessEnv;
}

export class SovereignXHardwareReplayStore {
  private readonly env: NodeJS.ProcessEnv;
  private readonly filePath?: string;

  constructor(options: SovereignXHardwareReplayStoreOptions = {}) {
    this.env = options.env ?? process.env;
    this.filePath = options.filePath;
  }

  append(snapshot: SovereignXHardwareSnapshot): SovereignXHardwareReplayRecord {
    const storePath = this.resolveStorePath();
    ensureParentDirectory(storePath);

    const records = this.list(storePath);
    const record: SovereignXHardwareReplayRecord = {
      sequence: records.length + 1,
      recordedAt: new Date(snapshot.governor.state.lastUpdatedAtMs).toISOString(),
      snapshot,
    };
    appendFileSync(storePath, `${JSON.stringify(record)}\n`, 'utf8');
    return record;
  }

  list(storePath = this.resolveStorePath()): SovereignXHardwareReplayRecord[] {
    if (!existsSync(storePath)) {
      return [];
    }

    const content = readFileSync(storePath, 'utf8');
    return content
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => JSON.parse(line) as SovereignXHardwareReplayRecord);
  }

  summary(): SovereignXHardwareReplaySummary {
    const storePath = this.resolveStorePath();
    const records = this.list(storePath);
    const recentRecords = records.slice(-5).map((record) => this.describeRecord(record));
    const latest = records.length > 0 ? records[records.length - 1] : null;

    return {
      available: records.length > 0,
      storePath,
      entryCount: records.length,
      latest: latest ? this.describeRecord(latest) : null,
      recentRecords,
    };
  }

  private resolveStorePath(): string {
    if (this.filePath?.trim()) {
      return path.resolve(this.filePath.trim());
    }

    const envPath = this.env.SOVEREIGNX_HARDWARE_REPLAY_STORE?.trim();
    if (envPath) {
      return path.resolve(envPath);
    }

    const home = this.env.USERPROFILE || this.env.HOME || '.';
    return path.join(home, '.sovereignx', 'hardware-replay.jsonl');
  }

  private describeRecord(record: SovereignXHardwareReplayRecord) {
    return {
      sequence: record.sequence,
      recordedAt: record.recordedAt,
      source: record.snapshot.source,
      sourceDetail: record.snapshot.sourceDetail,
      decision: record.snapshot.cycle.decision,
    };
  }
}

export function createSovereignXHardwareReplayStore(
  options: SovereignXHardwareReplayStoreOptions = {},
): SovereignXHardwareReplayStore {
  return new SovereignXHardwareReplayStore(options);
}

function ensureParentDirectory(storePath: string): void {
  const directory = path.dirname(storePath);
  mkdirSync(directory, { recursive: true });
}
