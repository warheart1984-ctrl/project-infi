import { describe, expect, it } from 'vitest';

import {
  AuthorityLedger,
  ExecutionSpanManager,
  GovernanceEnforcementEngine,
  IntentLedger,
} from './index.js';

describe('Tri-Strata governed memory', () => {
  it('intent ledger is append-only with verifiable chain', () => {
    const ledger = new IntentLedger();
    ledger.append({
      operator_id: 'op-1',
      semantic_goal: 'Prove RLS L1 boot',
      constraints: ['no destructive writes'],
      success_criteria: ['sealed boot'],
      horizon: 'short',
      signature: 'sig-v1',
    });
    const v2 = ledger.append({
      operator_id: 'op-1',
      semantic_goal: 'Prove RLS L1 boot',
      constraints: ['no destructive writes', 'fail-closed spine'],
      success_criteria: ['sealed boot'],
      horizon: 'short',
      signature: 'sig-v2',
    });
    expect(v2.version).toBe(2);
    expect(ledger.verifyChain()).toBe(true);
  });

  it('authority cannot exceed intent binding and revokes immediately', () => {
    const intents = new IntentLedger();
    const intent = intents.append({
      operator_id: 'op-1',
      semantic_goal: 'governed run',
      constraints: [],
      success_criteria: [],
      horizon: 'short',
      signature: 'i-sig',
    });
    const auth = new AuthorityLedger();
    const token = auth.issue({
      issued_by: 'governance',
      issued_to: 'agent-1',
      capabilities: ['execute'],
      scope: {
        resources: ['corridor:nova-dev'],
        time_limit_ms: Date.now() + 60_000,
        intent_version: intent.version,
      },
      delegation_chain: ['governance'],
    });
    expect(auth.validate(token.token_id, 'execute').ok).toBe(true);
    auth.revoke(token.token_id);
    expect(auth.validate(token.token_id, 'execute').ok).toBe(false);
  });

  it('execution span requires intent + authority references on every trace step', () => {
    const intents = new IntentLedger();
    const intent = intents.append({
      operator_id: 'op-1',
      semantic_goal: 'trace test',
      constraints: [],
      success_criteria: [],
      horizon: 'short',
      signature: 'i-sig',
    });
    const auth = new AuthorityLedger();
    const token = auth.issue({
      issued_by: 'governance',
      issued_to: 'agent-1',
      capabilities: ['execute'],
      scope: {
        resources: ['*'],
        time_limit_ms: Date.now() + 60_000,
        intent_version: intent.version,
      },
      delegation_chain: [],
    });
    const spans = new ExecutionSpanManager();
    const span = spans.startSpan({
      intent_version: intent.version,
      authority_token_id: token.token_id,
    });
    const engine = new GovernanceEnforcementEngine(intents, auth);
    const step = {
      timestamp: Date.now(),
      step_type: 'reasoning' as const,
      content: 'plan step',
      justification: 'aligned with operator goal',
      references: {
        intent_version: intent.version,
        authority_token_id: token.token_id,
      },
    };
    engine.validateTraceStep(step);
    spans.recordTrace(span.span_id, step);
    expect(spans.get(span.span_id)?.trace).toHaveLength(1);
  });
});
