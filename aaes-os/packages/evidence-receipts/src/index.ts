import { createHash } from 'node:crypto';

export type EvidenceReceiptKind = 'fault' | 'patch' | 'mri' | 'trust' | 'attestation' | 'runtime' | 'generic';

export interface EvidenceReceiptInput {
  claimLabel: string;
  subsystem: string;
  evidenceRefs: string[];
  subject: unknown;
  kind?: EvidenceReceiptKind;
  issuedAt?: string;
}

export interface EvidenceReceipt {
  receiptId: string;
  kind: EvidenceReceiptKind;
  claimLabel: string;
  subsystem: string;
  evidenceRefs: string[];
  subjectHash: string;
  issuedAt: string;
}

export function createEvidenceReceipt(input: EvidenceReceiptInput): EvidenceReceipt {
  const evidenceRefs = [...input.evidenceRefs];
  const subjectHash = hashJson(input.subject);
  const kind = input.kind ?? inferKind(input.subsystem, input.claimLabel);
  const receiptId = `evidence:${createHash('sha3-256')
    .update([input.claimLabel, input.subsystem, evidenceRefs.join(','), subjectHash].join('|'), 'utf8')
    .digest('hex')}`;

  return {
    receiptId,
    kind,
    claimLabel: input.claimLabel,
    subsystem: input.subsystem,
    evidenceRefs,
    subjectHash,
    issuedAt: input.issuedAt ?? new Date().toISOString(),
  };
}

export function createReceiptsForSubjects(inputs: EvidenceReceiptInput[]): EvidenceReceipt[] {
  return inputs.map((input) => createEvidenceReceipt(input));
}

export interface CenReceiptSubject {
  receiptId: string;
  transitionId: string;
  verdict: string;
  reasonCode: string;
  receiptHash: string;
}

export interface MriEvidenceReceiptInput {
  evidenceId: string;
  provenance: 'document' | 'system_log' | 'interview' | 'policy_artifact' | 'hearsay';
  recency: number;
  reliability: number;
  crossEvidenceConsistency: number;
  subject: unknown;
}

export function createCenEvidenceReceipt(subject: CenReceiptSubject): EvidenceReceipt {
  return createEvidenceReceipt({
    claimLabel: `cen:${subject.verdict.toLowerCase()}:${subject.reasonCode.toLowerCase()}`,
    subsystem: 'constitutional-enforcement-node',
    evidenceRefs: [subject.receiptId, subject.transitionId, subject.receiptHash],
    subject,
    kind: 'runtime',
  });
}

export function createMriEvidenceReceipt(input: MriEvidenceReceiptInput): EvidenceReceipt {
  return createEvidenceReceipt({
    claimLabel: 'mri-evidence-provenance',
    subsystem: 'mri-instrument',
    evidenceRefs: [
      input.evidenceId,
      `provenance:${input.provenance}`,
      `recency:${input.recency}`,
      `reliability:${input.reliability}`,
      `crossEvidenceConsistency:${input.crossEvidenceConsistency}`,
    ],
    subject: input.subject,
    kind: 'mri',
  });
}

export function verifyReceiptHash(receipt: EvidenceReceipt): boolean {
  return receipt.subjectHash.startsWith('sha3-256:') && receipt.receiptId.startsWith('evidence:');
}

function inferKind(subsystem: string, claimLabel: string): EvidenceReceiptKind {
  const value = `${subsystem} ${claimLabel}`.toLowerCase();
  if (value.includes('mri')) return 'mri';
  if (value.includes('trust')) return 'trust';
  if (value.includes('attestation')) return 'attestation';
  if (value.includes('runtime')) return 'runtime';
  if (value.includes('patch')) return 'patch';
  if (value.includes('fault')) return 'fault';
  return 'generic';
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
