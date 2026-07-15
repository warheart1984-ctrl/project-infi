import { describe, expect, it, vi } from 'vitest';

import { CepOrchestratorClient } from './cepOrchestratorClient';

describe('CepOrchestratorClient', () => {
  it('posts CEP artifacts and syncs the selected view state', async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetchImpl = vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url.endsWith('/api/cep/artifacts/promotion-request')) {
        return jsonResponse({
          id: 'cep-promo-1',
          kind: 'promotion-request',
          title: 'Promotion Request',
          source: 'platform-web',
          recordedAt: '2026-07-11T00:00:00.000Z',
          payload: { step: 'request' },
        });
      }
      if (url.endsWith('/api/cep/artifacts/replay-job')) {
        return jsonResponse({
          id: 'cep-replay-1',
          kind: 'replay-job',
          title: 'Replay Job',
          source: 'platform-web',
          relatedArtifactId: 'cep-promo-1',
          recordedAt: '2026-07-11T00:01:00.000Z',
          payload: { step: 'replay' },
        });
      }
      if (url.endsWith('/api/cep/artifacts/decision')) {
        return jsonResponse({
          id: 'cep-decision-1',
          kind: 'decision',
          title: 'Decision',
          source: 'platform-web',
          relatedArtifactId: 'cep-replay-1',
          recordedAt: '2026-07-11T00:02:00.000Z',
          payload: { step: 'decision' },
        });
      }
      if (url.endsWith('/api/cep/view-state') && init?.method === 'PATCH') {
        return jsonResponse({
          viewState: {
            selectedKind: 'decision',
            selectedArtifactId: 'cep-decision-1',
            updatedAt: '2026-07-11T00:03:00.000Z',
            source: 'remote',
          },
        });
      }
      if (url.endsWith('/api/cep/artifacts/export.json')) {
        return jsonResponse({
          storePath: 'ops-console/.runtime/cep-artifacts.jsonl',
          entryCount: 3,
          countsByKind: { 'promotion-request': 1, 'replay-job': 1, decision: 1 },
          records: [],
          recentRecords: [],
          viewState: {
            selectedKind: 'decision',
            selectedArtifactId: 'cep-decision-1',
            updatedAt: '2026-07-11T00:03:00.000Z',
            source: 'remote',
          },
        });
      }
      if (url.endsWith('/api/cep/view-state') && (!init || init.method === 'GET')) {
        return jsonResponse({
          viewState: {
            selectedKind: 'decision',
            selectedArtifactId: 'cep-decision-1',
            updatedAt: '2026-07-11T00:03:00.000Z',
            source: 'remote',
          },
        });
      }
      throw new Error(`Unexpected request: ${url}`);
    }) as unknown as typeof fetch;

    const client = new CepOrchestratorClient({ baseUrl: '', fetchImpl });
    const bundle = await client.syncBundle({
      promotionRequest: { kind: 'promotion-request' },
      replayJob: { kind: 'replay-job' },
      decision: { kind: 'decision' },
    });

    expect(bundle.promotionRequest.id).toBe('cep-promo-1');
    expect(bundle.replayJob.relatedArtifactId).toBe('cep-promo-1');
    expect(bundle.decision.relatedArtifactId).toBe('cep-replay-1');
    expect(bundle.viewState.selectedArtifactId).toBe('cep-decision-1');
    expect(calls.map((call) => call.url)).toEqual([
      '/api/cep/artifacts/promotion-request',
      '/api/cep/artifacts/replay-job',
      '/api/cep/artifacts/decision',
      '/api/cep/view-state',
    ]);
  });
});

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  });
}
