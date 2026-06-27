import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import {
  AuthorityLedger,
  ExecutionSpanManager,
  GovernanceEnforcementEngine,
  IntentLedger,
  completeSpan,
  createIntent,
  issueAuthority,
  recordTrace,
  replay,
  startSpan,
} from './index.js';

const fixturePath = join(
  dirname(fileURLToPath(import.meta.url)),
  '../../../../tests/fixtures/coordination_bottlenecks.md',
);

function freshStack() {
  const intentLedger = new IntentLedger();
  const authorityLedger = new AuthorityLedger();
  const spanManager = new ExecutionSpanManager();
  const governance = new GovernanceEnforcementEngine(intentLedger, authorityLedger);
  return { intentLedger, authorityLedger, spanManager, governance };
}

function summarizeTopThree(text: string): string {
  const headings = text
    .split('\n')
    .filter((line) => line.startsWith('## '))
    .map((line) => line.replace('## ', '').trim());
  return headings.slice(0, 3).join('; ');
}

describe('Vertical Slice', () => {
  it('creates intent with verifiable chain', () => {
    const { intentLedger } = freshStack();
    const intent = createIntent(
      'Summarize bottlenecks',
      ['read_only'],
      'operator-ts',
      { intentLedger },
    );
    expect(intent.version).toBe(1);
    expect(intentLedger.verifyChain()).toBe(true);
  });

  it('issues authority bound to intent version', () => {
    const { intentLedger, authorityLedger } = freshStack();
    const intent = createIntent('goal', [], 'op', { intentLedger });
    const auth = issueAuthority(intent.version, ['summarize'], 'gov', { authorityLedger });
    expect(authorityLedger.validate(auth.token.token_id, 'summarize').ok).toBe(true);
  });

  it('records trace steps with justification', () => {
    const stack = freshStack();
    const intent = createIntent('trace', [], 'op', stack);
    const auth = issueAuthority(intent.version, ['execute'], 'gov', stack);
    const span = startSpan(intent.version, auth.token.token_id, stack);
    recordTrace(
      span.span_id,
      {
        step_type: 'reasoning',
        content: 'ok',
        justification: 'required justification text',
      },
      intent.version,
      auth.token.token_id,
      stack,
    );
    const updated = stack.spanManager.get(span.span_id);
    expect(updated?.trace).toHaveLength(1);
  });

  it('replays completed span successfully', () => {
    const stack = freshStack();
    const fixture = readFileSync(fixturePath, 'utf-8');
    const intent = createIntent(
      'Summarize the top 3 coordination bottlenecks in this document.',
      ['read_fixture_only'],
      'operator-ts',
      stack,
    );
    const auth = issueAuthority(
      intent.version,
      ['read_document', 'summarize', 'cluster'],
      'gov',
      stack,
    );
    const span = startSpan(intent.version, auth.token.token_id, stack);
    const summary = summarizeTopThree(fixture);

    recordTrace(
      span.span_id,
      { step_type: 'reasoning', content: summary, justification: 'Stub summarizer.' },
      intent.version,
      auth.token.token_id,
      stack,
    );
    completeSpan(span.span_id, stack);

    const result = replay(span.span_id, stack);
    expect(result.success).toBe(true);
    expect(summary).toContain('Handoffs between teams');
    expect(summary).toContain('Unclear priorities');
    expect(summary).toContain('Tool fragmentation');
  });
});
