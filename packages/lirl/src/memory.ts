import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import path from 'node:path';

/** File-backed governed memory for LIRL v0.1 (substitutes empty `governed_memory/` top-level). */
export interface MemoryRecord {
  key: string;
  value: unknown;
  writtenAt: string;
  intentId: string;
  actorId: string;
  receiptId: string;
}

export class GovernedMemoryStore {
  private readonly filePath: string;
  private rows: MemoryRecord[] = [];

  constructor(rootDir: string) {
    mkdirSync(rootDir, { recursive: true });
    this.filePath = path.join(rootDir, 'memory.jsonl');
    this.load();
  }

  private load(): void {
    if (!existsSync(this.filePath)) {
      this.rows = [];
      return;
    }
    const text = readFileSync(this.filePath, 'utf8').trim();
    if (!text) {
      this.rows = [];
      return;
    }
    this.rows = text
      .split('\n')
      .filter(Boolean)
      .map((line) => JSON.parse(line) as MemoryRecord);
  }

  private persist(): void {
    const body = this.rows.map((row) => JSON.stringify(row)).join('\n') + (this.rows.length ? '\n' : '');
    writeFileSync(this.filePath, body, 'utf8');
  }

  write(record: MemoryRecord): MemoryRecord {
    this.rows.push(record);
    this.persist();
    return structuredClone(record);
  }

  list(): MemoryRecord[] {
    return this.rows.map((row) => structuredClone(row));
  }

  getByKey(key: string): MemoryRecord | undefined {
    const matches = this.rows.filter((row) => row.key === key);
    const latest = matches.at(-1);
    return latest ? structuredClone(latest) : undefined;
  }

  clear(): void {
    this.rows = [];
    this.persist();
  }

  get path(): string {
    return this.filePath;
  }
}
