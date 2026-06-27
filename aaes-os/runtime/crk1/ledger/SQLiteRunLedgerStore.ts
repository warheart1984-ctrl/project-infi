import { createHash } from 'node:crypto';
import { mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname } from 'node:path';

import type { InvariantResult } from '../governance/types.js';
import type { Fault, Receipt, RunContext } from '../types.js';
import type { RunLedgerStore } from './RunLedgerStore.js';

type SQLiteDatabase = {
  exec(sql: string): void;
  prepare(sql: string): {
    run(...values: unknown[]): unknown;
    get(...values: unknown[]): Record<string, unknown> | undefined;
    all(...values: unknown[]): Array<Record<string, unknown>>;
  };
  close(): void;
};

function loadDatabaseSync(): new (path: string) => SQLiteDatabase {
  try {
    const require = createRequire(import.meta.url);
    return require('node:sqlite').DatabaseSync as new (path: string) => SQLiteDatabase;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`SQLiteRunLedgerStore requires Node's node:sqlite runtime support: ${message}`);
  }
}

function receiptHash(ctx: RunContext, result: unknown): string {
  const payload = JSON.stringify({
    runId: ctx.id,
    payload: ctx.payload,
    spans: ctx.spans.map((s) => ({ type: s.type, data: s.data })),
    result,
  });
  return createHash('sha256').update(payload).digest('hex');
}

function readJson<T>(row: Record<string, unknown> | undefined, field: string): T | undefined {
  if (!row) return undefined;
  const value = row[field];
  if (typeof value !== 'string') return undefined;
  return JSON.parse(value) as T;
}

/**
 * SQLite-backed RunLedgerStore for durable CRK-1 receipts and faults.
 *
 * The implementation lazy-loads `node:sqlite` so older Node runtimes can still
 * import the module and use non-SQLite stores.
 */
export class SQLiteRunLedgerStore implements RunLedgerStore {
  private readonly db: SQLiteDatabase;

  constructor(path: string) {
    mkdirSync(dirname(path), { recursive: true });
    const DatabaseSync = loadDatabaseSync();
    this.db = new DatabaseSync(path);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS receipts (
        run_id TEXT PRIMARY KEY,
        receipt_json TEXT NOT NULL,
        created_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS faults (
        run_id TEXT PRIMARY KEY,
        fault_json TEXT NOT NULL,
        timestamp TEXT NOT NULL
      );
    `);
  }

  async recordReceipt(ctx: RunContext, result: unknown): Promise<Receipt> {
    const receipt: Receipt = {
      runId: ctx.id,
      hash: receiptHash(ctx, result),
      spans: [...ctx.spans],
      result,
      createdAt: new Date().toISOString(),
    };
    this.db
      .prepare(
        `INSERT OR REPLACE INTO receipts (run_id, receipt_json, created_at)
         VALUES (?, ?, ?)`,
      )
      .run(receipt.runId, JSON.stringify(receipt), receipt.createdAt);
    return receipt;
  }

  async recordFault(ctx: RunContext, fault: InvariantResult): Promise<Fault> {
    const record: Fault = {
      runId: ctx.id,
      invariantId: fault.invariantId ?? 'INV.UNKNOWN',
      message: fault.message ?? 'Invariant violation',
      timestamp: new Date().toISOString(),
    };
    this.db
      .prepare(
        `INSERT OR REPLACE INTO faults (run_id, fault_json, timestamp)
         VALUES (?, ?, ?)`,
      )
      .run(record.runId, JSON.stringify(record), record.timestamp);
    return record;
  }

  getReceipt(runId: string): Receipt | undefined {
    return readJson<Receipt>(
      this.db.prepare('SELECT receipt_json FROM receipts WHERE run_id = ?').get(runId),
      'receipt_json',
    );
  }

  getFault(runId: string): Fault | undefined {
    return readJson<Fault>(
      this.db.prepare('SELECT fault_json FROM faults WHERE run_id = ?').get(runId),
      'fault_json',
    );
  }

  listReceipts(): Receipt[] {
    return this.db
      .prepare('SELECT receipt_json FROM receipts ORDER BY created_at ASC, run_id ASC')
      .all()
      .map((row) => readJson<Receipt>(row, 'receipt_json'))
      .filter((receipt): receipt is Receipt => receipt !== undefined);
  }

  listFaults(): Fault[] {
    return this.db
      .prepare('SELECT fault_json FROM faults ORDER BY timestamp ASC, run_id ASC')
      .all()
      .map((row) => readJson<Fault>(row, 'fault_json'))
      .filter((fault): fault is Fault => fault !== undefined);
  }

  close(): void {
    this.db.close();
  }
}
