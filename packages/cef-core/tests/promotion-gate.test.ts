import { describe, expect, it } from 'vitest';
import {
  assertPromotionAllowed,
  claimExceedsEvidence,
} from '../src/promotionGate.js';
import { validOelEvidence } from './fixtures.js';

describe('assertPromotionAllowed (claim≠evidence)', () => {
  it('allows hold with pending checks', () => {
    const evidence = validOelEvidence({
      verification: {
        checks: [
          { id: 'check-security', result: 'pending' },
          { id: 'check-audit', result: 'passed' },
        ],
      },
      promotion: { decision: 'hold', signature: null, timestamp: null },
    });
    const result = assertPromotionAllowed(evidence);
    expect(result.allowed).toBe(true);
    expect(claimExceedsEvidence(evidence)).toBe(false);
  });

  it('rejects approved while checks pending', () => {
    const evidence = validOelEvidence({
      verification: {
        checks: [
          { id: 'check-security', result: 'pending' },
          { id: 'check-audit', result: 'passed' },
        ],
      },
      promotion: {
        decision: 'approved',
        signature: 'sig-test',
        timestamp: '2026-07-31T21:00:00.000Z',
      },
    });
    const result = assertPromotionAllowed(evidence);
    expect(result.allowed).toBe(false);
    expect(result.pendingCheckIds).toContain('check-security');
    expect(claimExceedsEvidence(evidence)).toBe(true);
  });

  it('rejects approved without signature', () => {
    const evidence = validOelEvidence({
      verification: {
        checks: [{ id: 'check-audit', result: 'passed' }],
      },
      promotion: {
        decision: 'approved',
        signature: null,
        timestamp: '2026-07-31T21:00:00.000Z',
      },
    });
    expect(assertPromotionAllowed(evidence).allowed).toBe(false);
  });

  it('allows approved with all checks passed and signature', () => {
    const evidence = validOelEvidence({
      verification: {
        checks: [
          { id: 'check-integrity', result: 'passed' },
          { id: 'check-security', result: 'passed' },
        ],
      },
      promotion: {
        decision: 'approved',
        signature: 'sig-test',
        timestamp: '2026-07-31T21:00:00.000Z',
      },
    });
    expect(assertPromotionAllowed(evidence).allowed).toBe(true);
    expect(claimExceedsEvidence(evidence)).toBe(false);
  });
});
