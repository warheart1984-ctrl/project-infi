import { describe, expect, it } from 'vitest';

import { runOmegaStressHarness } from './index.js';

describe('omega stress harness', () => {
  it('produces deterministic stress counts and sovereignty receipts', () => {
    const result = runOmegaStressHarness({ floodCount: 25 });

    expect(result.scenarios).toEqual([
      'malformed_payloads',
      'replay_attacks',
      'threshold_skirt_attempts',
      'high_frequency_floods',
      'conflicting_distributed_writes',
      'partial_trust_corrupted_tokens',
    ]);
    expect(result.counts.total).toBeGreaterThanOrEqual(25);
    expect(result.counts.denied).toBeGreaterThan(0);
    expect(result.sovereigntyEntries.length).toBeGreaterThan(0);
    expect(result.deterministic).toBe(true);
  });
});
