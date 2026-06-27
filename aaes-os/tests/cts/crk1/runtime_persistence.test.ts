import { createRequire } from 'node:module';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { afterEach, describe, expect, it } from 'vitest';

import {
  FileTraceSink,
  SQLiteRunLedgerStore,
  TraceBus,
  UCRRuntime,
} from '../../../runtime/crk1/index.js';

const tempDirs: string[] = [];

function makeTempDir(): string {
  const dir = mkdtempSync(path.join(tmpdir(), 'aaes-crk1-'));
  tempDirs.push(dir);
  return dir;
}

function sqliteAvailable(): boolean {
  try {
    createRequire(import.meta.url)('node:sqlite');
    return true;
  } catch {
    return false;
  }
}

afterEach(() => {
  while (tempDirs.length > 0) {
    const dir = tempDirs.pop()!;
    rmSync(dir, { recursive: true, force: true });
  }
});

describe('CRK-1 runtime persistence wiring', () => {
  it.runIf(sqliteAvailable())('persists receipts through SQLiteRunLedgerStore', async () => {
    const ledgerPath = path.join(makeTempDir(), 'run-ledger.sqlite3');
    const firstLedger = new SQLiteRunLedgerStore(ledgerPath);
    const runtime = new UCRRuntime({ ledger: firstLedger });

    const result = await runtime.execute({ id: 'run-sqlite-1', payload: { hello: 'aaes' } });

    expect(result.ok).toBe(true);
    expect(firstLedger.getReceipt('run-sqlite-1')?.result).toEqual({ echo: { hello: 'aaes' } });
    firstLedger.close();

    const secondLedger = new SQLiteRunLedgerStore(ledgerPath);
    expect(secondLedger.listReceipts()).toHaveLength(1);
    expect(secondLedger.getReceipt('run-sqlite-1')?.runId).toBe('run-sqlite-1');
    secondLedger.close();
  });

  it('writes trace spans through FileTraceSink', async () => {
    const tracePath = path.join(makeTempDir(), 'trace.jsonl');
    const runtime = new UCRRuntime({ trace: new TraceBus(new FileTraceSink(tracePath)) });

    const result = await runtime.execute({ id: 'run-trace-1', payload: { hello: 'trace' } });

    expect(result.ok).toBe(true);
    const events = readFileSync(tracePath, 'utf8')
      .trim()
      .split('\n')
      .map((line) => JSON.parse(line) as { runId: string; type: string });
    expect(events.map((event) => event.type)).toEqual(['init', 'execute', 'finalize']);
    expect(events.every((event) => event.runId === 'run-trace-1')).toBe(true);
  });
});
