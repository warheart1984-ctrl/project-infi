import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { validateProfile } from '../src/validators/validateProfile.js';
import {
  validCelEvidence,
  validCoreEvidence,
  validCrecEvidence,
  validModelEvalEvidence,
  validOelEvidence,
  validSecurityEvidence,
} from './fixtures.js';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '../../..');

describe('validateProfile', () => {
  it('accepts valid OEL evidence', () => {
    const result = validateProfile('OEL', validOelEvidence());
    expect(result.valid).toBe(true);
    expect(result.profile).toBe('OEL');
  });

  it('rejects OEL evidence missing oel payload', () => {
    const result = validateProfile('OEL', validCoreEvidence({ type: 'OEL' }));
    expect(result.valid).toBe(false);
  });

  it('rejects unknown profile name', () => {
    const result = validateProfile('NotAProfile', validOelEvidence());
    expect(result.valid).toBe(false);
    expect(result.errors?.[0]?.message).toMatch(/unknown CEF profile/i);
  });

  it('rejects CREC profile when type is OEL', () => {
    const result = validateProfile('CREC', validOelEvidence());
    expect(result.valid).toBe(false);
  });

  it('validates docs baseline example as OEL (may hold pending digests)', () => {
    const path = join(
      repoRoot,
      'docs/release/cef/examples/evidence-baseline-v1.0.json',
    );
    const example = JSON.parse(readFileSync(path, 'utf8')) as unknown;
    const result = validateProfile('OEL', example);
    expect(result.valid).toBe(true);
  });

  it('accepts valid CREC evidence', () => {
    expect(validateProfile('CREC', validCrecEvidence()).valid).toBe(true);
  });

  it('accepts valid CEL evidence', () => {
    expect(validateProfile('CEL', validCelEvidence()).valid).toBe(true);
  });

  it('accepts valid Security evidence', () => {
    expect(validateProfile('Security', validSecurityEvidence()).valid).toBe(
      true,
    );
  });

  it('accepts valid ModelEval evidence', () => {
    expect(validateProfile('ModelEval', validModelEvalEvidence()).valid).toBe(
      true,
    );
  });

  it('rejects CREC fixture under OEL profile', () => {
    expect(validateProfile('OEL', validCrecEvidence()).valid).toBe(false);
  });
});
