import { describe, expect, it } from 'vitest';

import {
  collapseGovernanceLayers,
  createFileLawOfLawsAdapter,
  createLawOfLawsLedger,
  recordMetaConstitutionalCollapsePod,
  verifyCrossLayerConsistency,
  verifyLawOfLawsLedger,
} from './index.js';
import { mkdtempSync, rmSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';

describe('meta-constitutional calculus', () => {
  it('records the meta_constitutional_collapse POD with the required receipt fields', () => {
    const pod = recordMetaConstitutionalCollapsePod();

    expect(pod.podId).toBe('meta_constitutional_collapse');
    expect(pod.discoveredBy).toBe('jon halstead sigil 1001');
    expect(pod.rewardMultiplier).toBe(500);
    expect(pod.classification).toBe('foundational');
    expect(pod.invariantImpact).toBe('meta_governance');
    expect(pod.receipt.receiptId).toMatch(/^evidence:/);
  });

  it('collapses CML, CVM, and substrate layers into CML-15 meta-invariants', () => {
    const collapse = collapseGovernanceLayers();

    expect(collapse.generativeCoreId).toBe('CML-15');
    expect(collapse.sourceLayers.cml).toHaveLength(14);
    expect(collapse.sourceLayers.cvm).toHaveLength(13);
    expect(collapse.metaInvariants.map((inv) => inv.id)).toEqual([
      'meta-invariant:cross-layer-consistency',
      'meta-invariant:finite-generative-core',
      'meta-invariant:constitutional-fixed-point',
      'meta-invariant:governed-emergence',
    ]);
    expect(collapse.singularity.stability).toBe('stable_fixed_point');
  });

  it('hash chains the law-of-laws ledger', () => {
    const ledger = createLawOfLawsLedger();
    const first = ledger.append({
      entryType: 'meta_invariant',
      subjectId: 'meta-invariant:cross-layer-consistency',
      payload: { state: 'recorded' },
    });
    const second = ledger.append({
      entryType: 'constitutional_singularity',
      subjectId: 'constitutional-singularity:CML-15',
      payload: { state: 'anchored' },
    });

    expect(first.previousHash).toBeNull();
    expect(second.previousHash).toBe(first.entryHash);
    expect(ledger.entries()).toHaveLength(2);
    expect(verifyLawOfLawsLedger(ledger.entries())).toBe(true);
  });

  it('persists law-of-laws entries through an adapter and verifies cross-layer consistency', () => {
    let saved = [] as ReturnType<ReturnType<typeof createLawOfLawsLedger>['entries']>;
    const ledger = createLawOfLawsLedger({
      load: () => saved,
      save: (entries) => {
        saved = entries;
      },
    });
    ledger.append({
      entryType: 'collapse_record',
      subjectId: 'CML-15',
      payload: collapseGovernanceLayers(),
    });

    expect(saved).toHaveLength(1);
    expect(verifyCrossLayerConsistency()).toBe(true);
  });

  it('persists law-of-laws entries through the file adapter', () => {
    const tempDir = mkdtempSync(path.join(os.tmpdir(), 'aaes-law-of-laws-'));
    try {
      const adapter = createFileLawOfLawsAdapter(path.join(tempDir, 'law.json'));
      const first = createLawOfLawsLedger(adapter);
      first.append({
        entryType: 'pod',
        subjectId: 'meta_constitutional_collapse',
        payload: { status: 'recorded' },
        issuedAt: '2026-06-18T22:02:00.000Z',
      });

      const second = createLawOfLawsLedger(adapter);
      expect(second.entries()).toHaveLength(1);
      expect(second.entries()[0]?.subjectId).toBe('meta_constitutional_collapse');
      expect(verifyLawOfLawsLedger(second.entries())).toBe(true);
    } finally {
      rmSync(tempDir, { recursive: true, force: true });
    }
  });
});
