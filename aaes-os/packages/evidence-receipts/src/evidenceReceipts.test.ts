import { describe, expect, it } from 'vitest';

import {
  createCenEvidenceReceipt,
  createEvidenceReceipt,
  createMriEvidenceReceipt,
  verifyReceiptHash,
} from './index.js';

describe('evidence receipts', () => {
  it('creates deterministic receipt IDs from claim and evidence references', () => {
    const first = createEvidenceReceipt({
      claimLabel: 'trust-root-sealed',
      subsystem: 'trust-root',
      evidenceRefs: ['boot:ok', 'measurement:h_trust_root'],
      subject: { hTrustRoot: 'sha3-256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' },
    });
    const second = createEvidenceReceipt({
      claimLabel: 'trust-root-sealed',
      subsystem: 'trust-root',
      evidenceRefs: ['boot:ok', 'measurement:h_trust_root'],
      subject: { hTrustRoot: 'sha3-256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' },
    });

    expect(first.receiptId).toBe(second.receiptId);
    expect(first.claimLabel).toBe('trust-root-sealed');
    expect(first.evidenceRefs).toEqual(['boot:ok', 'measurement:h_trust_root']);
  });

  it('maps runtime and MRI claims into receipt kinds', () => {
    const runtime = createEvidenceReceipt({
      claimLabel: 'runtime-initialized',
      subsystem: 'runtime-law-spine',
      evidenceRefs: ['registration:ok'],
      subject: { allowed: true },
    });
    const mri = createEvidenceReceipt({
      claimLabel: 'mri-continuity-report',
      subsystem: 'mri-instrument',
      evidenceRefs: ['mri:comparison'],
      subject: { continuity: 72 },
    });

    expect(runtime.kind).toBe('runtime');
    expect(mri.kind).toBe('mri');
  });

  it('creates CEN and MRI provenance receipts with verifiable hashes', () => {
    const cen = createCenEvidenceReceipt({
      receiptId: 'cen:abc',
      verdict: 'DENY',
      reasonCode: 'INVARIANT_VIOLATION',
      transitionId: 'transition:deny',
      receiptHash: 'sha3-256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    });
    const mri = createMriEvidenceReceipt({
      evidenceId: 'evidence:mri:1',
      provenance: 'system_log',
      recency: 0.92,
      reliability: 0.88,
      crossEvidenceConsistency: 0.81,
      subject: { continuity: 72 },
    });

    expect(cen.kind).toBe('runtime');
    expect(cen.evidenceRefs).toContain('cen:abc');
    expect(mri.kind).toBe('mri');
    expect(mri.evidenceRefs).toContain('evidence:mri:1');
    expect(verifyReceiptHash(mri)).toBe(true);
  });
});
