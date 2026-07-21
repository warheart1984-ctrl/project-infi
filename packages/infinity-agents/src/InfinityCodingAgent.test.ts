import { describe, expect, it, vi } from 'vitest';
import type { CodingRouter, GovernedChatResponse } from '@aaes-os/governed-runtime';

import { ConformanceGate } from './chain/ConformanceGate.js';
import { CorpusAdmitter } from './chain/CorpusAdmitter.js';
import { EGL1Checker } from './chain/EGL1Checker.js';
import { InfinityCodingAgent } from './InfinityCodingAgent.js';

function mockRouter(responses: string[]): CodingRouter {
  let call = 0;
  return {
    execute: vi.fn(async () => {
      const text = responses[call] ?? `step-output-${call}`;
      call += 1;
      const traceId = `trace-${call}`;
      return {
        intentId: traceId,
        backendName: 'mock',
        trace: {
          traceId,
          intentId: traceId,
          actorId: 'actor-1',
          policyIds: [],
          timestamps: { createdAt: Date.now() },
        },
        output: { text, tokensIn: 1, tokensOut: 1, latencyMs: 1 },
        governance: { policyIds: [], violations: [] },
      } satisfies GovernedChatResponse;
    }),
  } as unknown as CodingRouter;
}

describe('InfinityCodingAgent — 13-step chain', () => {
  it('completes all 13 steps in order', async () => {
    const router = mockRouter(['step one\nstep two', 'result-one', 'result-two']);
    const agent = new InfinityCodingAgent(router, { actorId: 'actor-1', role: 'developer' });

    const result = await agent.solve('build feature');

    expect(result.steps).toEqual(['step one', 'step two']);
    expect(result.stepResults).toHaveLength(2);
    expect(result.stepResults[0]?.bundle).toBeDefined();
    expect(result.stepResults[0]?.replayReport?.matches).toBe(true);
    expect(result.stepResults[0]?.egl1Report?.passed).toBe(true);
    expect(result.stepResults[0]?.conformanceReport?.admitted).toBe(true);
    expect(agent.getCorpusAdmitter().getCorpus()).toHaveLength(2);
  });

  it('ConformanceGate blocks apply when EGL-1 fails', async () => {
    const gate = new ConformanceGate();
    const checker = new EGL1Checker();
    const bundle = {
      bundle_id: 'eb-1',
      step_index: 0,
      actor_id: 'actor-1',
      action: 'APPLY_PATCH',
      output_hash: 'abc',
      evidence_refs: ['trace-1'],
      collected_at: new Date().toISOString(),
    };

    const egl1Report = checker.evaluate(
      {
        stepIndex: 0,
        actorId: 'actor-1',
        action: 'APPLY_PATCH',
        output: null,
        trace_id: 'trace-1',
        drift: 0.5,
      },
      bundle,
    );

    expect(() =>
      gate.check(egl1Report, {
        report_id: 'rr-1',
        bundle_id: 'eb-1',
        replay_hash: 'abc',
        original_hash: 'abc',
        matches: true,
        verified_at: new Date().toISOString(),
      }),
    ).toThrow(/CONFORMANCE GATE/);
  });

  it('CorpusAdmitter rejects non-admitted artifacts', () => {
    const admitter = new CorpusAdmitter();

    expect(() =>
      admitter.admit({
        report_id: 'conf-1',
        egl1_report_id: 'egl1-1',
        replay_report_id: 'rr-1',
        admitted: false,
        certified_at: new Date().toISOString(),
      }),
    ).toThrow(/cannot admit non-admitted artifact/);
  });

  it('drift above 0.036 fails EGL-1 drift class', () => {
    const checker = new EGL1Checker();
    const report = checker.evaluate(
      {
        stepIndex: 0,
        actorId: 'actor-1',
        action: 'PLAN_STEP',
        output: 'ok',
        trace_id: 'trace-1',
        drift: 0.05,
      },
      {
        bundle_id: 'eb-1',
        step_index: 0,
        actor_id: 'actor-1',
        action: 'PLAN_STEP',
        output_hash: 'abc',
        evidence_refs: ['trace-1'],
        collected_at: new Date().toISOString(),
      },
    );

    expect(report.classes.drift).toBe(false);
    expect(report.passed).toBe(false);
  });
});
