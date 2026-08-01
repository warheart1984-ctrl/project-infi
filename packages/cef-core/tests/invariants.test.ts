import { describe, expect, it } from 'vitest';
import {
  allInvariantsPassed,
  checkInvariants,
} from '../src/invariants.js';
import { validCoreEvidence } from './fixtures.js';

describe('CEF charter invariants (structural)', () => {
  it('passes all invariants for valid evidence', () => {
    const checks = checkInvariants(validCoreEvidence());
    expect(checks.every((c) => c.passed)).toBe(true);
    expect(allInvariantsPassed(validCoreEvidence())).toBe(true);
  });

  it('Invariant 1 — promotion fails when required fields missing', () => {
    const { authority: _a, ...missing } = validCoreEvidence();
    const claim = checkInvariants(missing).find(
      (c) => c.id === 'claim-bound-to-evidence',
    );
    expect(claim?.passed).toBe(false);
  });

  it('Invariant 2 — replay instructions must exist and be non-empty', () => {
    const checks = checkInvariants(
      validCoreEvidence({ replay: { instructions: '   ' } }),
    );
    expect(checks.find((c) => c.id === 'replayable')?.passed).toBe(false);
  });

  it('Invariant 3 — audit.visibility must be valid', () => {
    const checks = checkInvariants(
      validCoreEvidence({
        audit: { visibility: 'secret' as 'internal' },
      }),
    );
    expect(checks.find((c) => c.id === 'auditable')?.passed).toBe(false);
  });

  it('Invariant 4 — authority fields required', () => {
    const checks = checkInvariants(
      validCoreEvidence({
        authority: { carId: '', actorId: 'a', role: 'r' },
      }),
    );
    expect(checks.find((c) => c.id === 'authority-bound')?.passed).toBe(false);
  });

  it('Invariant 5 — version must follow semver pattern', () => {
    const checks = checkInvariants(validCoreEvidence({ version: 'v1' }));
    expect(checks.find((c) => c.id === 'versioned')?.passed).toBe(false);
  });

  it('Invariant 6 — promotion.decision must be governed enum', () => {
    const checks = checkInvariants(
      validCoreEvidence({
        promotion: { decision: 'maybe' as 'hold' },
      }),
    );
    expect(checks.find((c) => c.id === 'governed-promotion')?.passed).toBe(
      false,
    );
  });
});
