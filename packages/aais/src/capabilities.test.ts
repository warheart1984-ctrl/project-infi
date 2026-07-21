import { describe, expect, it } from 'vitest';

import {
  composeReferenceRuntime,
  listAAISCapabilities,
  resolveImplementationGap,
  resolveRoutingHint,
  routing,
} from './capabilities.js';

describe('AAIS capabilities', () => {
  it('includes the runtime composer, conformance generator, and gap resolver', () => {
    const capabilityNames = listAAISCapabilities().map((capability) => capability.name);

    expect(capabilityNames).toContain('Reference Runtime Composer');
    expect(capabilityNames).toContain('Conformance Suite Generator');
    expect(capabilityNames).toContain('Implementation Gap Resolver');
  });

  it('composes a normalized reference runtime order', () => {
    const runtime = composeReferenceRuntime(['  runtime core  ', '', 'ledger', 'runtime core']);

    expect(runtime).toEqual({
      flow: ['llm', 'jarvis', 'nova'],
      components: ['runtime core', 'ledger'],
      name: 'Reference Runtime Composer',
    });
  });

  it('resolves implementation gaps in intent order', () => {
    const resolution = resolveImplementationGap(
      ['runtime core', 'ledger', 'evidence'],
      ['ledger', 'evidence archive'],
    );

    expect(resolution.missing).toEqual(['runtime core', 'evidence']);
    expect(resolution.prioritizedWork).toEqual([
      { priority: 1, item: 'runtime core' },
      { priority: 2, item: 'evidence' },
    ]);
    expect(resolution.summary).toBe('2 gap(s) identified');
  });

  it('provides constitutional routing hints for prompt classes', () => {
    expect(routing.smallPrompt.preferredModel).toBe('qwen-3b');
    expect(routing.largePrompt.preferredModel).toBe('qwen-7b');
    expect(resolveRoutingHint({ payload: 'tiny fix' })).toEqual(routing.smallPrompt);
    expect(resolveRoutingHint({ payload: 'deep reasoning and architecture review' })).toEqual(
      routing.largePrompt,
    );
  });
});
