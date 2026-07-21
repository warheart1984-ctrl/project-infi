import { describe, expect, it } from 'vitest';

import { TriCoreBus } from '@aaes-os/tri-core-protocol';

import { AAISRuntime } from './AAISRuntime.js';

describe('AAISRuntime', () => {
  it('exposes the simplified llm to jarvis to nova flow', () => {
    const runtime = new AAISRuntime();

    expect((runtime as unknown as { describeFlow: () => string[] }).describeFlow()).toEqual([
      'llm',
      'jarvis',
      'nova',
    ]);
  });

  it('routes a check through llm, jarvis, then nova', () => {
    const bus = new TriCoreBus();
    const runtime = new AAISRuntime({ bus });

    const message = runtime.sendAAISCheck({ prompt: 'simplify aais' });

    expect(message?.type).toBe('AAIS_CHECK');
    expect(message?.from).toBe('agent');
    expect(message?.to).toBe('governance');
    expect(message?.payload).toMatchObject({
      payload: { prompt: 'simplify aais' },
      flow: ['llm', 'jarvis', 'nova'],
      validation: { passed: true },
      routingHint: {
        preferredModel: 'qwen-3b',
        reason: 'small prompt',
      },
      provenance: {
        capabilityName: 'Capability Discovery Engine',
        capabilityFile: 'packages/aais/src/capabilities.ts',
        resolver: 'AAISRuntime.executeAAISCheck',
        routingHint: {
          preferredModel: 'qwen-3b',
          reason: 'small prompt',
        },
      },
    });
  });

  it('stops before nova when the governed runtime is frozen', () => {
    const bus = new TriCoreBus({ frozen: true });
    const runtime = new AAISRuntime({ bus });

    const result = runtime.executeAAISCheck({ prompt: 'hold fast' });

    expect(result.validation).toMatchObject({
      passed: false,
      reason: 'AAIS blocked by constitutional freeze',
    });
    expect(result.stages).toEqual([
      { stage: 'llm', passed: true },
      {
        stage: 'jarvis',
        passed: false,
        reason: 'AAIS blocked by constitutional freeze',
        details: expect.any(Array),
      },
      { stage: 'nova', passed: false },
    ]);
    expect(result.message).toBeNull();
  });

  it('exposes routing provenance for docs and router consumption', () => {
    const runtime = new AAISRuntime();

    const provenance = runtime.getAAISProvenance({
      surface: 'docs-site',
      payload: 'document the constitutional proof surface with provenance tracing and routing',
    });

    expect(provenance.capabilityName).toBe('Capability Discovery Engine');
    expect(provenance.capabilityFile).toBe('packages/aais/src/capabilities.ts');
    expect(provenance.routingHint?.preferredModel).toBe('qwen-7b');
  });
});
