import { describe, expect, it } from 'vitest';

import { AuthorityLevel } from './AuthorityLevel.js';
import { SovrenAuthority } from './SovrenAuthority.js';

describe('SovrenAuthority', () => {
  it('issues and verifies a valid token', () => {
    const sovren = new SovrenAuthority('test-law-key');
    const token = sovren.issue('actor-1', AuthorityLevel.OPERATOR);

    expect(sovren.verify(token)).toBe(true);
  });

  it('rejects a tampered token signature', () => {
    const sovren = new SovrenAuthority('test-law-key');
    const token = sovren.issue('actor-1', AuthorityLevel.OPERATOR);

    token.signature = 'deadbeef'.repeat(8);
    expect(sovren.verify(token)).toBe(false);
  });

  it('rejects an expired token', () => {
    const sovren = new SovrenAuthority('test-law-key');
    const token = sovren.issue('actor-1', AuthorityLevel.OPERATOR, -1);

    expect(sovren.verify(token)).toBe(false);
  });

  it('authorize() throws if level is insufficient', () => {
    const sovren = new SovrenAuthority('test-law-key');
    const token = sovren.issue('actor-1', AuthorityLevel.OBSERVER);

    expect(() => sovren.authorize(token, AuthorityLevel.OPERATOR)).toThrow(/requires level 2/);
  });

  it('signEnvelope() produces deterministic HMAC', () => {
    const sovren = new SovrenAuthority('test-law-key');
    const envelope = { b: 2, a: 1, c: 3 };

    const first = sovren.signEnvelope(envelope);
    const second = sovren.signEnvelope({ c: 3, a: 1, b: 2 });

    expect(first).toBe(second);
    expect(first).toHaveLength(64);
  });
});
