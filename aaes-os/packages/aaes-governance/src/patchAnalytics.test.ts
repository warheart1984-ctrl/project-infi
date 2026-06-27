import { describe, expect, it } from 'vitest';

import { PatchAnalytics } from './patchAnalytics.js';

describe('PatchAnalytics', () => {
  it('computes effectiveness as reduction in recurrence', () => {
    const analytics = new PatchAnalytics();

    analytics.recordSample({
      patchId: 'PATCH_OUTPUT_SHAPE_001',
      timestamp: '2026-06-18T10:00:00.000Z',
      preRecurrence: 10,
      postRecurrence: 2,
    });

    analytics.recordSample({
      patchId: 'PATCH_DETERMINISM_001',
      timestamp: '2026-06-18T11:00:00.000Z',
      preRecurrence: 0,
      postRecurrence: 0,
    });

    const timeline = analytics.getTimeline();

    expect(timeline).toHaveLength(2);
    expect(timeline[0]).toEqual({
      patchId: 'PATCH_OUTPUT_SHAPE_001',
      timestamp: '2026-06-18T10:00:00.000Z',
      preRecurrence: 10,
      postRecurrence: 2,
      effectiveness: 0.8,
    });
    expect(timeline[1]?.effectiveness).toBe(1);
  });
});
