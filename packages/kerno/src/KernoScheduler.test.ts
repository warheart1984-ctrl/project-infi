import { describe, expect, it, vi } from 'vitest';

import { KernoScheduler } from './KernoScheduler.js';

describe('KernoScheduler', () => {
  it('reserves and releases slots correctly', () => {
    const scheduler = new KernoScheduler(2);
    const slotId = scheduler.reserve('actor-1', 'coding-plan');

    expect(slotId).toMatch(/^slot_/);
    expect(() => scheduler.release(slotId)).not.toThrow();
  });

  it('throws when slot pool is exhausted', () => {
    const scheduler = new KernoScheduler(1);
    scheduler.reserve('actor-1', 'a');
    expect(() => scheduler.reserve('actor-2', 'b')).toThrow(/slot pool exhausted/);
  });

  it('calculates cache-hit-rate correctly', () => {
    const scheduler = new KernoScheduler(4);
    const slot1 = scheduler.reserve('actor-1', 'alpha');
    const slot2 = scheduler.reserve('actor-1', 'alpha');
    const slot3 = scheduler.reserve('actor-1', 'beta');
    scheduler.release(slot1);
    scheduler.release(slot2);
    scheduler.release(slot3);

    expect(scheduler.getCacheHitRate()).toBeCloseTo(1 / 3, 5);
  });

  it('emits IMMUNE_RUNTIME_ALERT after 5 consecutive low cache-hit steps', () => {
    const scheduler = new KernoScheduler(10);
    const handler = vi.fn();
    scheduler.on('IMMUNE_RUNTIME_ALERT', handler);

    const intents = ['a', 'b', 'c', 'd', 'e', 'f'];
    for (const intent of intents) {
      const slot = scheduler.reserve('actor-1', intent);
      scheduler.release(slot);
    }

    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler.mock.calls[0]?.[0]).toMatchObject({
      consecutive_low_steps: 5,
    });
  });

  it('resets consecutive counter when rate recovers', () => {
    const scheduler = new KernoScheduler(20);
    const handler = vi.fn();
    scheduler.on('IMMUNE_RUNTIME_ALERT', handler);

    for (let i = 0; i < 5; i++) {
      const slot = scheduler.reserve('actor-1', `intent-${i}`);
      scheduler.release(slot);
    }

    for (let i = 0; i < 10; i++) {
      const slot = scheduler.reserve('actor-1', 'same-intent');
      scheduler.release(slot);
    }

    expect(handler).toHaveBeenCalledTimes(1);
  });
});
