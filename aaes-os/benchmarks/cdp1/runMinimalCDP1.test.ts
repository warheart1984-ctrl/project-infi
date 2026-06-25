import { describe, expect, it } from 'vitest';

import { runMinimalCDP1 } from '../../benchmarks/cdp1/runMinimalCDP1.js';

describe('CDP-1 minimal benchmark', () => {
  it('runs baseline vs perturbed and returns driftScore 0 or 1', async () => {
    const result = await runMinimalCDP1();
    expect(result).toHaveProperty('baseline');
    expect(result).toHaveProperty('perturbed');
    expect([0, 1]).toContain(result.driftScore);
  });
});
