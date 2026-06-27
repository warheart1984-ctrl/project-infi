import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

export type SovereigntyEventType =
  | 'authority_token_used'
  | 'bypass_attempt'
  | 'denied_transition'
  | 'freeze_decision'
  | 'mandatory_review_decision';

export interface SovereigntyLedgerEntryInput {
  eventType: SovereigntyEventType;
  subjectId: string;
  payload: unknown;
  issuedAt?: string;
}

export interface SovereigntyLedgerEntry extends Required<SovereigntyLedgerEntryInput> {
  sequence: number;
  previousHash: string | null;
  entryHash: string;
}

export interface SovereigntyLedger {
  append: (input: SovereigntyLedgerEntryInput) => SovereigntyLedgerEntry;
  entries: () => SovereigntyLedgerEntry[];
}

export function createSovereigntyLedger(): SovereigntyLedger {
  const entries: SovereigntyLedgerEntry[] = [];
  return {
    append(input) {
      const previousHash = entries.at(-1)?.entryHash ?? null;
      const base = {
        sequence: entries.length + 1,
        eventType: input.eventType,
        subjectId: input.subjectId,
        payload: input.payload,
        issuedAt: input.issuedAt ?? new Date().toISOString(),
        previousHash,
      };
      const entry: SovereigntyLedgerEntry = { ...base, entryHash: hashEntry(base) };
      entries.push(entry);
      return entry;
    },
    entries() {
      return [...entries];
    },
  };
}

export function createFileSovereigntyLedger(filePath: string): SovereigntyLedger {
  const entries = readEntries(filePath);
  return {
    append(input) {
      const previousHash = entries.at(-1)?.entryHash ?? null;
      const base = {
        sequence: entries.length + 1,
        eventType: input.eventType,
        subjectId: input.subjectId,
        payload: input.payload,
        issuedAt: input.issuedAt ?? new Date().toISOString(),
        previousHash,
      };
      const entry: SovereigntyLedgerEntry = { ...base, entryHash: hashEntry(base) };
      entries.push(entry);
      writeEntries(filePath, entries);
      return entry;
    },
    entries() {
      return [...entries];
    },
  };
}

export function appendSovereigntyEntry(
  ledger: SovereigntyLedger,
  input: SovereigntyLedgerEntryInput,
): SovereigntyLedgerEntry {
  return ledger.append(input);
}

export function verifySovereigntyChain(entries: SovereigntyLedgerEntry[]): boolean {
  return entries.every((entry, index) => {
    const { entryHash, ...base } = entry;
    const previousOk = index === 0
      ? entry.previousHash === null
      : entry.previousHash === entries[index - 1]?.entryHash;
    return previousOk && entryHash === hashEntry(base);
  });
}

function hashEntry(value: unknown): string {
  return `sha3-256:${createHash('sha3-256').update(stableStringify(value), 'utf8').digest('hex')}`;
}

function readEntries(filePath: string): SovereigntyLedgerEntry[] {
  if (!existsSync(filePath)) return [];
  const parsed = JSON.parse(readFileSync(filePath, 'utf8')) as unknown;
  return Array.isArray(parsed) ? (parsed as SovereigntyLedgerEntry[]) : [];
}

function writeEntries(filePath: string, entries: SovereigntyLedgerEntry[]): void {
  mkdirSync(path.dirname(filePath), { recursive: true });
  writeFileSync(filePath, `${JSON.stringify(entries, null, 2)}\n`, 'utf8');
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map((entry) => stableStringify(entry)).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}
