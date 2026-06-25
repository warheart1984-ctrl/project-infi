import type { RunLedgerStore } from './RunLedgerStore.js';

/**
 * SQLite-backed RunLedgerStore — Phase 6 persistence.
 * Not implemented in v1.0; use InMemoryRunLedgerStore.
 */
export class SQLiteRunLedgerStore implements RunLedgerStore {
  async recordReceipt(): Promise<never> {
    throw new Error('SQLiteRunLedgerStore not implemented (Phase 6).');
  }

  async recordFault(): Promise<never> {
    throw new Error('SQLiteRunLedgerStore not implemented (Phase 6).');
  }

  getReceipt(): undefined {
    return undefined;
  }

  getFault(): undefined {
    return undefined;
  }

  listReceipts() {
    return [];
  }

  listFaults() {
    return [];
  }
}
