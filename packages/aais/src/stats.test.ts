import { describe, expect, it, beforeEach } from 'vitest';

import {
  getAAISRoutingStats,
  recordRoutingEvent,
  resetAAISRoutingStats,
} from './stats.js';

describe('AAIS routing stats', () => {
  beforeEach(() => {
    resetAAISRoutingStats();
  });

  it('aggregates routing decisions by capability and model', () => {
    recordRoutingEvent({
      capabilityName: 'Capability Discovery Engine',
      model: 'qwen-3b',
      overrideApplied: false,
      hintUsed: true,
      heuristicFallback: false,
    });
    recordRoutingEvent({
      capabilityName: 'Capability Discovery Engine',
      model: 'qwen-7b',
      overrideApplied: true,
      hintUsed: false,
      heuristicFallback: true,
    });

    const stats = getAAISRoutingStats();

    expect(stats.byCapability).toEqual([
      {
        capabilityName: 'Capability Discovery Engine',
        total: 2,
        byModel: { 'qwen-3b': 1, 'qwen-7b': 1 },
        overrides: 1,
        hintsUsed: 1,
        heuristicFallbacks: 1,
      },
    ]);
  });
});
