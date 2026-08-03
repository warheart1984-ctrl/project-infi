import { describe, expect, it } from 'vitest';
import { validateEvidence } from '../src/validators/validateEvidence.js';
import { validCoreEvidence } from './fixtures.js';

describe('validateEvidence (core schema)', () => {
  it('accepts a valid evidence object', () => {
    const result = validateEvidence(validCoreEvidence());
    expect(result.valid).toBe(true);
    expect(result.errors).toBeNull();
  });

  it('rejects missing required fields', () => {
    const { id: _id, ...missingId } = validCoreEvidence();
    const result = validateEvidence(missingId);
    expect(result.valid).toBe(false);
    expect(result.errors?.some((e) => e.keyword === 'required')).toBe(true);
  });

  it('rejects wrong types', () => {
    const result = validateEvidence(
      validCoreEvidence({ version: 1 as unknown as string }),
    );
    expect(result.valid).toBe(false);
  });

  it('rejects invalid profile type enum', () => {
    const result = validateEvidence(
      validCoreEvidence({ type: 'NOT_A_PROFILE' as never }),
    );
    expect(result.valid).toBe(false);
  });

  it('rejects empty replay instructions', () => {
    const result = validateEvidence(
      validCoreEvidence({ replay: { instructions: '' } }),
    );
    expect(result.valid).toBe(false);
  });

  it('rejects promotion without decision', () => {
    const base = validCoreEvidence();
    const { decision: _d, ...promo } = base.promotion;
    const result = validateEvidence({ ...base, promotion: promo });
    expect(result.valid).toBe(false);
  });
});
