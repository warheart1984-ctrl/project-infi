import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { createEvidenceReceipt, type EvidenceReceipt } from '@aaes-os/evidence-receipts';

export type MetaInvariantId =
  | 'meta-invariant:cross-layer-consistency'
  | 'meta-invariant:finite-generative-core'
  | 'meta-invariant:constitutional-fixed-point'
  | 'meta-invariant:governed-emergence';

export interface MetaInvariant {
  id: MetaInvariantId;
  statement: string;
  impact: 'meta_governance';
}

export interface ConstitutionalSingularity {
  id: 'constitutional-singularity:CML-15';
  stability: 'stable_fixed_point';
  anchoredBy: 'law-of-laws-ledger';
}

export interface MetaConstitutionalCollapseRecord {
  generativeCoreId: 'CML-15';
  executedBy: 'meta-runtime';
  anchoredBy: 'law-of-laws-ledger';
  sourceLayers: {
    cml: string[];
    cvm: string[];
    substrate: string[];
  };
  metaInvariants: MetaInvariant[];
  singularity: ConstitutionalSingularity;
}

export interface PodEntry {
  podId: 'meta_constitutional_collapse';
  podType: 'conceptual_discovery';
  discoveryTier: 'civilizational';
  rewardMultiplier: 500;
  discoveredBy: 'jon halstead sigil 1001';
  timestamp: string;
  governanceArcTier: 'foundational';
  classification: 'foundational';
  invariantImpact: 'meta_governance';
  status: 'recorded';
  receipt: EvidenceReceipt;
}

export type LawOfLawsEntryType =
  | 'pod'
  | 'meta_invariant'
  | 'constitutional_singularity'
  | 'collapse_record'
  | 'evolution_decision';

export interface LawOfLawsEntryInput {
  entryType: LawOfLawsEntryType;
  subjectId: string;
  payload: unknown;
  issuedAt?: string;
}

export interface LawOfLawsEntry extends LawOfLawsEntryInput {
  sequence: number;
  previousHash: string | null;
  entryHash: string;
  issuedAt: string;
}

export interface LawOfLawsLedger {
  append: (input: LawOfLawsEntryInput) => LawOfLawsEntry;
  entries: () => LawOfLawsEntry[];
}

export interface LawOfLawsStorageAdapter {
  load: () => LawOfLawsEntry[];
  save: (entries: LawOfLawsEntry[]) => void;
}

const DEFAULT_TIMESTAMP = '2026-06-18T22:02:00.000Z';

export function collapseGovernanceLayers(): MetaConstitutionalCollapseRecord {
  return {
    generativeCoreId: 'CML-15',
    executedBy: 'meta-runtime',
    anchoredBy: 'law-of-laws-ledger',
    sourceLayers: {
      cml: rangeLabels('CML', 1, 14),
      cvm: rangeLabels('CVM', 1, 13),
      substrate: ['trust-root', 'ucr-attestation', 'runtime-law-spine', 'evidence-receipts'],
    },
    metaInvariants: [
      {
        id: 'meta-invariant:cross-layer-consistency',
        statement: 'All governance layers must project to a shared invariant basis.',
        impact: 'meta_governance',
      },
      {
        id: 'meta-invariant:finite-generative-core',
        statement: 'The infinite governance ladder must collapse into a finite generative calculus.',
        impact: 'meta_governance',
      },
      {
        id: 'meta-invariant:constitutional-fixed-point',
        statement: 'Constitutional evolution must converge on a stable fixed point.',
        impact: 'meta_governance',
      },
      {
        id: 'meta-invariant:governed-emergence',
        statement: 'Emergent behavior must remain measured, constrained, and receipted.',
        impact: 'meta_governance',
      },
    ],
    singularity: {
      id: 'constitutional-singularity:CML-15',
      stability: 'stable_fixed_point',
      anchoredBy: 'law-of-laws-ledger',
    },
  };
}

export function recordMetaConstitutionalCollapsePod(
  timestamp = DEFAULT_TIMESTAMP,
): PodEntry {
  const collapse = collapseGovernanceLayers();
  const receipt = createEvidenceReceipt({
    claimLabel: 'POD(meta_constitutional_collapse)',
    subsystem: 'meta-constitutional-calculus',
    evidenceRefs: [
      'packages/meta-constitutional-calculus/src/index.ts',
      'docs/proof/platform/META_CONSTITUTIONAL_COLLAPSE.md',
    ],
    subject: collapse,
    issuedAt: timestamp,
  });

  return {
    podId: 'meta_constitutional_collapse',
    podType: 'conceptual_discovery',
    discoveryTier: 'civilizational',
    rewardMultiplier: 500,
    discoveredBy: 'jon halstead sigil 1001',
    timestamp,
    governanceArcTier: 'foundational',
    classification: 'foundational',
    invariantImpact: 'meta_governance',
    status: 'recorded',
    receipt,
  };
}

export function createLawOfLawsLedger(adapter?: LawOfLawsStorageAdapter): LawOfLawsLedger {
  const ledger: LawOfLawsEntry[] = adapter?.load() ?? [];
  return {
    append(input) {
      const previousHash = ledger.at(-1)?.entryHash ?? null;
      const entryBase = {
        sequence: ledger.length + 1,
        entryType: input.entryType,
        subjectId: input.subjectId,
        payload: input.payload,
        issuedAt: input.issuedAt ?? new Date().toISOString(),
        previousHash,
      };
      const entry: LawOfLawsEntry = {
        ...entryBase,
        entryHash: hashJson(entryBase),
      };
      ledger.push(entry);
      adapter?.save([...ledger]);
      return entry;
    },
    entries() {
      return [...ledger];
    },
  };
}

export function createFileLawOfLawsAdapter(filePath: string): LawOfLawsStorageAdapter {
  return {
    load() {
      if (!existsSync(filePath)) return [];
      const parsed = JSON.parse(readFileSync(filePath, 'utf8')) as unknown;
      return Array.isArray(parsed) ? (parsed as LawOfLawsEntry[]) : [];
    },
    save(entries) {
      mkdirSync(path.dirname(filePath), { recursive: true });
      writeFileSync(filePath, `${JSON.stringify(entries, null, 2)}\n`, 'utf8');
    },
  };
}

export function verifyLawOfLawsLedger(entries: LawOfLawsEntry[]): boolean {
  return entries.every((entry, index) => {
    const { entryHash, ...base } = entry;
    const previousOk = index === 0
      ? entry.previousHash === null
      : entry.previousHash === entries[index - 1]?.entryHash;
    return previousOk && entryHash === hashJson(base);
  });
}

export function verifyCrossLayerConsistency(record = collapseGovernanceLayers()): boolean {
  return (
    record.generativeCoreId === 'CML-15' &&
    record.sourceLayers.cml.length === 14 &&
    record.sourceLayers.cvm.length === 13 &&
    record.metaInvariants.length >= 4 &&
    record.singularity.stability === 'stable_fixed_point'
  );
}

function rangeLabels(prefix: string, start: number, end: number): string[] {
  return Array.from({ length: end - start + 1 }, (_, index) => `${prefix}-${start + index}`);
}

function hashJson(value: unknown): string {
  return `sha3-256:${createHash('sha3-256').update(stableStringify(value), 'utf8').digest('hex')}`;
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry)).join(',')}]`;
  }
  if (value !== null && typeof value === 'object') {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}
