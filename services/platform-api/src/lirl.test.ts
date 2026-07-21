import { describe, expect, it } from 'vitest';

import { createApp } from './server.js';
import { resetLirlRuntimeForTests } from './lirlState.js';
import { platform } from './state.js';

describe('platform-api LIRL routes', () => {
  it('accepts lawful memory.write via POST /v1/lirl/intents', async () => {
    resetLirlRuntimeForTests();
    const session = platform.login('lirl-operator', 'balanced');
    const app = createApp();
    const server = app.listen(0);
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;

    try {
      const res = await fetch(`http://127.0.0.1:${port}/v1/lirl/intents`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-session-id': session.sessionId,
        },
        body: JSON.stringify({
          action: 'memory.write',
          payload: { key: 'platform-greeting', value: { text: 'ma-la' } },
        }),
      });

      expect(res.status).toBe(201);
      const body = (await res.json()) as {
        verdict: string;
        receiptId: string;
        memoryWritten: boolean;
        memoryKey: string;
      };
      expect(body.verdict).toBe('ACCEPT');
      expect(body.memoryWritten).toBe(true);
      expect(body.memoryKey).toBe('platform-greeting');
      expect(body.receiptId).toMatch(/^evidence:/);

      const memory = await fetch(`http://127.0.0.1:${port}/v1/lirl/memory/platform-greeting`, {
        headers: { 'x-session-id': session.sessionId },
      });
      expect(memory.status).toBe(200);
      const memoryBody = (await memory.json()) as {
        record: { receiptId: string; value: { text: string } };
      };
      expect(memoryBody.record.receiptId).toBe(body.receiptId);
      expect(memoryBody.record.value).toEqual({ text: 'ma-la' });
    } finally {
      server.close();
    }
  });

  it('rejects unlawful bypass via POST /v1/lirl/intents without writing memory', async () => {
    resetLirlRuntimeForTests();
    const session = platform.login('lirl-reject', 'balanced');
    const app = createApp();
    const server = app.listen(0);
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;

    try {
      const res = await fetch(`http://127.0.0.1:${port}/v1/lirl/intents`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-session-id': session.sessionId,
        },
        body: JSON.stringify({
          action: 'unlawful.bypass',
          payload: { key: 'secret', value: 'nope' },
          forceBypass: true,
        }),
      });

      expect(res.status).toBe(422);
      const body = (await res.json()) as {
        verdict: string;
        memoryWritten: boolean;
        reasons: string[];
        receiptId: string;
      };
      expect(body.verdict).toBe('REJECT');
      expect(body.memoryWritten).toBe(false);
      expect(body.reasons.length).toBeGreaterThan(0);
      expect(body.receiptId).toMatch(/^evidence:/);

      const memory = await fetch(`http://127.0.0.1:${port}/v1/lirl/memory/secret`, {
        headers: { 'x-session-id': session.sessionId },
      });
      expect(memory.status).toBe(404);
    } finally {
      server.close();
    }
  });
});
