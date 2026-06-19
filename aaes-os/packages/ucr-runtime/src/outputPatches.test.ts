import { describe, expect, it } from 'vitest';

import {
  applyOutputPatches,
  normalizeOutputShape,
  sanitizeDeterminism,
} from './outputPatches.js';

describe('normalizeOutputShape', () => {
  it('wraps string primitives', () => {
    expect(normalizeOutputShape('hello')).toEqual({ type: 'string', value: 'hello' });
  });

  it('passes through plain objects', () => {
    const obj = { ok: true };
    expect(normalizeOutputShape(obj)).toBe(obj);
  });
});

describe('sanitizeDeterminism', () => {
  it('replaces large numbers and rand key', () => {
    const input = { rand: 0.42, ts: 1_700_000_000_000, ok: true };
    expect(sanitizeDeterminism(input)).toEqual({
      rand: '<random>',
      ts: '<timestamp>',
      ok: true,
    });
  });
});

describe('applyOutputPatches', () => {
  it('normalizes then sanitizes', () => {
    expect(applyOutputPatches('x')).toEqual({ type: 'string', value: 'x' });
  });
});
