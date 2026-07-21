import { describe, expect, it, vi } from 'vitest';

import { NovaCodingShell } from '@aaes-os/nova-shell';

import { CodingAssistant } from './CodingAssistant.js';

describe('CodingAssistant', () => {
  it('runs AAIS before creating Nova', () => {
    const executeAAISCheck = vi.fn(() => ({ message: { ok: true } }));
    const assistant = new CodingAssistant(
      { execute: vi.fn() } as never,
      {
        describeFlow: () => ['llm', 'jarvis', 'nova'],
        describeCapabilities: () => [
          { name: 'Reference Runtime Composer' },
          { name: 'Conformance Suite Generator' },
          { name: 'Implementation Gap Resolver' },
        ],
        executeAAISCheck,
      } as never,
    );

    const nova = assistant.nova({ actorId: 'jon', role: 'developer' });

    expect(nova).toBeInstanceOf(NovaCodingShell);
    expect(executeAAISCheck).toHaveBeenCalledTimes(1);
    expect(executeAAISCheck).toHaveBeenCalledWith({
      surface: 'nova',
      flow: ['llm', 'jarvis', 'nova'],
      capabilities: expect.arrayContaining([
        'Reference Runtime Composer',
        'Conformance Suite Generator',
        'Implementation Gap Resolver',
      ]),
      payload: {
        identity: { actorId: 'jon', role: 'developer' },
        options: undefined,
      },
    });
  });

  it('forwards the user model preference to SovereignX', () => {
    const setOverride = vi.fn();
    const assistant = new CodingAssistant(
      { execute: vi.fn() } as never,
      {
        describeFlow: () => ['llm', 'jarvis', 'nova'],
        executeAAISCheck: vi.fn(() => ({ message: null })),
      } as never,
      {
        setOverride,
      } as never,
    );

    assistant.setModelPreference('qwen-7b');
    assistant.setModelPreference('auto');

    expect(setOverride).toHaveBeenNthCalledWith(1, 'qwen-7b');
    expect(setOverride).toHaveBeenNthCalledWith(2, null);
  });
});
