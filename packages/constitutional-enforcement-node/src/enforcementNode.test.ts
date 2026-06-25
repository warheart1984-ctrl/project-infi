import { describe, expect, it } from 'vitest';

import {
  ConstitutionalEnforcementNode,
  compileInvariantDsl,
  createResourceFloorInvariant,
  issueAuthorityToken,
  verifyEnforcementReceipt,
} from './index.js';

const baselineContext = {
  mriSnapshot: {
    continuity: 72,
    governance: 68,
    memory: 75,
    coordination: 63,
    confidence: 81,
  },
  actor: 'operator',
  runtimeContext: {
    corridorId: 'law-evolution',
    capabilities: ['law:propose', 'state:commit'],
  },
};

describe('ConstitutionalEnforcementNode', () => {
  it('allows safe transitions and commits them to the state store', () => {
    const node = new ConstitutionalEnforcementNode({
      invariants: [createResourceFloorInvariant('continuity', 50)],
    });

    const result = node.execute({
      transitionId: 'transition:safe',
      transitionType: 'state_update',
      payload: { continuity: 74 },
      requestedCapabilities: ['state:commit'],
      context: baselineContext,
    });

    expect(result.decision.verdict).toBe('ALLOW');
    expect(result.committed).toBe(true);
    expect(node.getState('transition:safe')).toEqual({ continuity: 74 });
    expect(result.receipt.receiptId).toMatch(/^cen:/);
    expect(result.receipt.previousReceiptHash).toBeNull();
  });

  it('denies invariant violations and hash chains enforcement receipts', () => {
    const node = new ConstitutionalEnforcementNode({
      invariants: [createResourceFloorInvariant('coordination', 60)],
    });

    const allowed = node.execute({
      transitionId: 'transition:prime',
      transitionType: 'state_update',
      payload: { coordination: 64 },
      requestedCapabilities: ['state:commit'],
      context: baselineContext,
    });
    const denied = node.execute({
      transitionId: 'transition:floor-breach',
      transitionType: 'state_update',
      payload: { coordination: 42 },
      requestedCapabilities: ['state:commit'],
      context: baselineContext,
    });

    expect(allowed.decision.verdict).toBe('ALLOW');
    expect(denied.decision.verdict).toBe('DENY');
    expect(denied.decision.reasonCode).toBe('INVARIANT_VIOLATION');
    expect(denied.committed).toBe(false);
    expect(denied.receipt.previousReceiptHash).toBe(allowed.receipt.receiptHash);
    expect(node.getState('transition:floor-breach')).toBeUndefined();
  });

  it('compiles the minimum invariant DSL bridge', () => {
    const invariant = compileInvariantDsl('require governance >= 70');
    const node = new ConstitutionalEnforcementNode({ invariants: [invariant] });

    const result = node.execute({
      transitionId: 'transition:dsl-deny',
      transitionType: 'law_mutation',
      payload: { law: 'soft invariant proposed' },
      requestedCapabilities: ['law:propose'],
      context: baselineContext,
    });

    expect(result.decision.verdict).toBe('DENY');
    expect(result.receipt.evaluations[0]?.invariantId).toBe('idsl:governance:min:70');
  });

  it('denies capability bypass attempts before invariant evaluation', () => {
    const node = new ConstitutionalEnforcementNode({
      invariants: [createResourceFloorInvariant('continuity', 50)],
    });

    const result = node.execute({
      transitionId: 'transition:bypass',
      transitionType: 'law_mutation',
      payload: { law: 'mutate outside authority' },
      requestedCapabilities: ['root:bypass'],
      context: baselineContext,
    });

    expect(result.decision.verdict).toBe('DENY');
    expect(result.decision.reasonCode).toBe('CAPABILITY_DENIED');
    expect(result.receipt.evaluations).toHaveLength(0);
  });

  it('exposes EP-1 lifecycle methods and categorizes allow, anomaly, replay, and token refusals', () => {
    const node = new ConstitutionalEnforcementNode({
      invariants: [createResourceFloorInvariant('continuity', 50)],
      issuedAt: () => '2026-06-18T22:45:00.000Z',
    });
    const transition = {
      transitionId: 'transition:lifecycle',
      transitionType: 'state_update' as const,
      payload: { continuity: 74 },
      requestedCapabilities: ['state:commit'],
      context: baselineContext,
    };

    const intercepted = node.intercept(transition);
    const evaluated = node.evaluate(intercepted);
    const allowed = node.allow(evaluated);
    const replayed = node.execute(transition);
    const malformed = node.execute({ ...transition, transitionId: '', payload: null });

    expect(allowed.receipt.category).toBe('allow');
    expect(allowed.receipt.stage).toBe('receipt');
    expect(verifyEnforcementReceipt(allowed.receipt)).toBe(true);
    expect(replayed.decision.reasonCode).toBe('REPLAY_DETECTED');
    expect(replayed.receipt.category).toBe('replay');
    expect(malformed.decision.reasonCode).toBe('MALFORMED_TRANSITION');
    expect(malformed.receipt.category).toBe('anomaly');
  });

  it('validates authority tokens and emits FREEZE or MANDATORY_REVIEW trigger actions', () => {
    const node = new ConstitutionalEnforcementNode({
      invariants: [
        {
          invariantId: 'trigger:freeze-low-confidence',
          evaluate: () => ({
            invariantId: 'trigger:freeze-low-confidence',
            passed: false,
            message: 'confidence below freeze floor',
            action: 'FREEZE',
          }),
        },
      ],
      issuedAt: () => '2026-06-18T22:45:00.000Z',
    });
    const token = issueAuthorityToken({
      tokenId: 'vt-1',
      tokenType: 'VT',
      scope: ['law:propose'],
      transitionId: 'transition:freeze',
      expiresAt: '2999-01-01T00:00:00.000Z',
    });

    const frozen = node.execute({
      transitionId: 'transition:freeze',
      transitionType: 'law_mutation',
      payload: { law: 'unsafe mutation' },
      requestedCapabilities: ['law:propose'],
      authorityToken: token,
      context: baselineContext,
    });
    const replayedToken = node.execute({
      transitionId: 'transition:new-token-replay',
      transitionType: 'law_mutation',
      payload: { law: 'reuse token' },
      requestedCapabilities: ['law:propose'],
      authorityToken: token,
      context: baselineContext,
    });

    expect(frozen.decision.verdict).toBe('DENY');
    expect(frozen.decision.action).toBe('FREEZE');
    expect(frozen.receipt.category).toBe('deny');
    expect(replayedToken.decision.reasonCode).toBe('TOKEN_REPLAYED');
    expect(replayedToken.receipt.category).toBe('token_refusal');
  });
});
