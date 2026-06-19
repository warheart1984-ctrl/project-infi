import { createServer, type Server } from 'node:http';

import { describe, expect, it, afterAll, beforeAll } from 'vitest';

import { app } from './server.js';

describe('GET /telemetry', () => {
  let server: Server;
  let baseUrl = '';

  beforeAll(async () => {
    await new Promise<void>((resolve) => {
      server = createServer(app);
      server.listen(0, '127.0.0.1', () => {
        const address = server.address();
        const port = typeof address === 'object' && address ? address.port : 4000;
        baseUrl = `http://127.0.0.1:${port}`;
        resolve();
      });
    });
  });

  afterAll(async () => {
    await new Promise<void>((resolve, reject) => {
      server.close((error) => {
        if (error) {
          reject(error);
          return;
        }
        resolve();
      });
    });
  });

  it('returns drift, topPatterns, and lastFaults keys', async () => {
    const response = await fetch(`${baseUrl}/telemetry`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      drift: { score: number; totalFaults: number; uniquePatterns: number };
      topPatterns: unknown[];
      lastFaults: unknown[];
      patchTimeline: unknown[];
    };

    expect(body.drift).toEqual(
      expect.objectContaining({
        score: expect.any(Number),
        totalFaults: expect.any(Number),
        uniquePatterns: expect.any(Number),
      }),
    );
    expect(body.drift.totalFaults).toBeGreaterThan(0);
    expect(Array.isArray(body.topPatterns)).toBe(true);
    expect(Array.isArray(body.lastFaults)).toBe(true);
    expect(Array.isArray(body.patchTimeline)).toBe(true);
  });

  it('exposes production health, readiness, request id, and security headers', async () => {
    const response = await fetch(`${baseUrl}/readiness`);
    expect(response.status).toBe(200);
    expect(response.headers.get('x-content-type-options')).toBe('nosniff');
    expect(response.headers.get('x-frame-options')).toBe('DENY');
    expect(response.headers.get('x-request-id')).toBeTruthy();

    const body = (await response.json()) as {
      ready: boolean;
      checks: { telemetry: boolean; cen: boolean; sovereigntyLedger: boolean; lawOfLawsLedger: boolean };
    };
    expect(body.ready).toBe(true);
    expect(body.checks).toEqual({
      telemetry: true,
      cen: true,
      sovereigntyLedger: true,
      lawOfLawsLedger: true,
    });
  });

  it('returns the seeded MRI operator assessment', async () => {
    const response = await fetch(`${baseUrl}/mri`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      comparison: {
        before: { scores: { continuity: number; confidence: number } };
        after: { scores: { continuity: number; confidence: number } };
        deltaState: Record<string, number>;
      };
      report: { summary: string };
    };

    expect(body.comparison.before.scores.continuity).toBeTypeOf('number');
    expect(body.comparison.after.scores.continuity).toBeGreaterThan(
      body.comparison.before.scores.continuity,
    );
    expect(body.comparison.after.scores.confidence).toBeGreaterThanOrEqual(
      body.comparison.before.scores.confidence,
    );
    expect(body.comparison.deltaState).toEqual(
      expect.objectContaining({
        R: expect.any(Number),
        K: expect.any(Number),
        G: expect.any(Number),
        D: expect.any(Number),
        X: expect.any(Number),
      }),
    );
    expect(body.report.summary).toContain('Continuity increased by');
  });

  it('returns recent document subsystem coverage for operators', async () => {
    const response = await fetch(`${baseUrl}/coverage`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      mappedDocuments: number;
      subsystems: string[];
      documents: { path: string; subsystem: string }[];
    };

    expect(body.mappedDocuments).toBe(38);
    expect(body.subsystems).toContain('trust-root');
    expect(body.subsystems).toContain('ucr-attestation');
    expect(body.subsystems).toContain('runtime-law-spine');
    expect(body.subsystems).toContain('evidence-receipts');
    expect(body.documents.some((doc) => doc.path === 'docs/contracts/AAES_OS_ARCHITECTURE_V1.md')).toBe(true);
  });

  it('returns the CEN enforcement demo receipt', async () => {
    const response = await fetch(`${baseUrl}/cen/demo`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      decision: { verdict: string; reasonCode: string };
      receipt: { receiptId: string; evaluations: unknown[]; mriSnapshotHash: string };
    };

    expect(body.decision.verdict).toBe('DENY');
    expect(body.decision.reasonCode).toBe('INVARIANT_VIOLATION');
    expect(body.receipt.receiptId).toMatch(/^cen:/);
    expect(body.receipt.mriSnapshotHash).toMatch(/^sha3-256:/);
    expect(body.receipt.evaluations.length).toBeGreaterThan(0);
  });

  it('returns the meta-constitutional collapse POD for operators', async () => {
    const response = await fetch(`${baseUrl}/pod/meta_constitutional_collapse`);
    expect(response.status).toBe(200);

    const body = (await response.json()) as {
      pod: { podId: string; rewardMultiplier: number; status: string };
      collapse: { generativeCoreId: string; metaInvariants: unknown[] };
    };

    expect(body.pod.podId).toBe('meta_constitutional_collapse');
    expect(body.pod.rewardMultiplier).toBe(500);
    expect(body.pod.status).toBe('recorded');
    expect(body.collapse.generativeCoreId).toBe('CML-15');
    expect(body.collapse.metaInvariants).toHaveLength(4);
  });

  it('returns CEN events, receipts, sovereignty ledger, NIMF forecast, and law-of-laws entries', async () => {
    const events = await fetch(`${baseUrl}/cen/events`);
    const eventsBody = (await events.json()) as { events: { receiptId: string }[] };
    const [receipt, missingReceipt, sovereignty, forecast, law] = await Promise.all([
      fetch(`${baseUrl}/cen/receipts/${encodeURIComponent(eventsBody.events[0]?.receiptId ?? '')}`),
      fetch(`${baseUrl}/cen/receipts/not-found`),
      fetch(`${baseUrl}/sovereignty-ledger`),
      fetch(`${baseUrl}/nimf/forecast`),
      fetch(`${baseUrl}/meta/law-of-laws`),
    ]);

    expect(events.status).toBe(200);
    expect(receipt.status).toBe(200);
    expect(missingReceipt.status).toBe(404);
    expect(sovereignty.status).toBe(200);
    expect(forecast.status).toBe(200);
    expect(law.status).toBe(200);

    expect(eventsBody.events.length).toBeGreaterThan(0);
    expect((await receipt.json()) as { receipt: { receiptId: string } }).toEqual(
      expect.objectContaining({ receipt: expect.objectContaining({ receiptId: expect.stringMatching(/^cen:/) }) }),
    );
    expect(((await sovereignty.json()) as { entries: unknown[] }).entries.length).toBeGreaterThan(0);
    expect(((await forecast.json()) as { forecast: { horizon: number } }).forecast.horizon).toBe(3);
    expect(((await law.json()) as { entries: unknown[] }).entries.length).toBeGreaterThan(0);
  });

  it('returns patch approval records as JSON for the operator console', async () => {
    const response = await fetch(`${baseUrl}/patches`);
    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toContain('application/json');

    const body = (await response.json()) as {
      patches: { patchId: string; status: string; proposedBy: string }[];
    };
    expect(body.patches.length).toBeGreaterThan(0);
    expect(body.patches[0]).toEqual(expect.objectContaining({
      patchId: expect.any(String),
      status: expect.any(String),
      proposedBy: expect.any(String),
    }));
  });

  it('accepts evolution proposal and evaluation requests', async () => {
    const proposed = await fetch(`${baseUrl}/evolution/propose`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ invariantId: 'INV-OPS', expression: 'require governance >= 70' }),
    });
    const evaluated = await fetch(`${baseUrl}/evolution/evaluate`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ invariantId: 'INV-OPS', expression: 'require governance >= 70' }),
    });

    expect(proposed.status).toBe(200);
    expect(evaluated.status).toBe(200);
    expect(((await proposed.json()) as { proposal: { status: string } }).proposal.status).toBe('proposed');
    expect(((await evaluated.json()) as { decision: { decision: string } }).decision.decision).toMatch(/promote|retain|revert/);
  });
});
