import { createServer, type Server } from 'node:http';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { afterAll, beforeEach, describe, expect, it } from 'vitest';

import { buildRelationshipTrustPacket } from '../../../packages/sovereignx-router/dist/index.js';
import { getCoriAlphaRepositoryRoot } from './coriAlpha.js';
import { createApp } from './server.js';
import { resetSovereignControlPlaneState } from './state.js';

describe('sovereign-control-plane', () => {
  let server: Server;
  let baseUrl = '';
  let coriAlphaRoot = '';
  let previousCoriAlphaRoot: string | undefined;

  beforeEach(async () => {
    resetSovereignControlPlaneState();
    previousCoriAlphaRoot = process.env.CORI_ALPHA_ROOT;
    coriAlphaRoot = mkdtempSync(join(tmpdir(), 'cori-alpha-'));
    process.env.CORI_ALPHA_ROOT = coriAlphaRoot;
    await new Promise<void>((resolve) => {
      server = createServer(createApp());
      server.listen(0, '127.0.0.1', () => {
        const address = server.address();
        const port = typeof address === 'object' && address ? address.port : 4000;
        baseUrl = `http://127.0.0.1:${port}`;
        resolve();
      });
    });
  });

  afterAll(async () => {
    if (!server) {
      if (coriAlphaRoot) {
        rmSync(coriAlphaRoot, { recursive: true, force: true });
      }
      return;
    }
    await new Promise<void>((resolve, reject) => {
      server.close((error) => {
        if (error) {
          reject(error);
          return;
        }
        resolve();
      });
    });
    if (previousCoriAlphaRoot === undefined) {
      delete process.env.CORI_ALPHA_ROOT;
    } else {
      process.env.CORI_ALPHA_ROOT = previousCoriAlphaRoot;
    }
    if (coriAlphaRoot) {
      rmSync(coriAlphaRoot, { recursive: true, force: true });
    }
  });

  it('exposes trust relationships and governance views', async () => {
    const response = await fetch(`${baseUrl}/trust/relationships?domain=safety`);
    expect(response.status).toBe(200);
    const body = (await response.json()) as { relationships: { relationshipId: string; trustResult: { band: string } }[]; summary: { count: number } };
    expect(body.summary.count).toBeGreaterThan(0);
    expect(body.relationships.some((relationship) => relationship.relationshipId === 'rel-model-safety')).toBe(true);

    const governance = await fetch(`${baseUrl}/trust/governance/rel-model-safety`);
    expect(governance.status).toBe(200);
    const governanceBody = (await governance.json()) as { relationshipId: string; trustResult: { band: string } };
    expect(governanceBody.relationshipId).toBe('rel-model-safety');
    expect(governanceBody.trustResult.band).toBe('high');
  });

  it('evaluates governed actions and records decisions', async () => {
    const response = await fetch(`${baseUrl}/governance/evaluate`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        actionId: 'action-1',
        actionType: 'routing',
        actorId: 'steward-1',
        relationshipId: 'rel-router-org',
        domain: 'ops',
        trustPacket: {
          relationshipId: 'rel-router-org',
          revision: 2,
          subjectId: 'org-acme',
          objectId: 'router-x',
          relationshipKind: 'trust-bearing',
          governanceLevel: 'enhanced',
          authorityChain: ['steward-1', 'kernel-1'],
          trust: {
            score: 0.84,
            band: 'high',
            evidenceIds: ['ev-router-tests', 'ev-router-proof-surface'],
          },
        },
        context: { candidateId: 'router-x' },
      }),
    });

    expect(response.status).toBe(200);
    const body = (await response.json()) as { result: string; governanceFactor: number; constraints: string[] };
    expect(body.result).toBe('allowed');
    expect(body.governanceFactor).toBeGreaterThan(0);
    expect(body.constraints.some((constraint) => constraint.includes('requires_trustScore'))).toBe(true);

    const decisionResponse = await fetch(`${baseUrl}/governance/decision`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        decisionId: 'decision-1',
        actionId: 'action-1',
        result: body.result,
        tier: 'Operations',
        domain: 'ops',
        trustPacket: {
          relationshipId: 'rel-router-org',
          revision: 2,
          subjectId: 'org-acme',
          objectId: 'router-x',
          relationshipKind: 'trust-bearing',
          governanceLevel: 'enhanced',
          authorityChain: ['steward-1', 'kernel-1'],
          trust: {
            score: 0.84,
            band: 'high',
            evidenceIds: ['ev-router-tests', 'ev-router-proof-surface'],
          },
        },
        reason: 'trust and evidence passed',
        constraintsApplied: body.constraints,
        decidedBy: 'kernel-1',
      }),
    });

    expect(decisionResponse.status).toBe(200);
    const decisionBody = (await decisionResponse.json()) as { ledgerEntryId: string; hash: string };
    expect(decisionBody.ledgerEntryId).toContain('ledger-');
    expect(decisionBody.hash).toHaveLength(64);
  });

  it('evaluates router decisions through the governance kernel and records canonical artifacts', async () => {
    const routeTrustPacket = buildRelationshipTrustPacket({
      relationshipId: 'rel-router-1',
      revision: 1,
      subjectId: 'org-router-1',
      objectId: 'router-x',
      relationshipKind: 'routing',
      governanceLevel: 'full',
      authorityChain: ['steward-1', 'kernel-1'],
      trust: {
        score: 0.84,
        band: 'high',
        evidenceIds: ['ev-1', 'ev-2', 'ev-3'],
        authority: { stewardId: 'steward-1' },
        provenance: { originSystem: 'relationship-ledger', method: 'assertion' },
      },
      ledgerEntryId: 'ledger-router-1',
      receiptId: 'receipt-router-1',
      capturedAt: '2026-07-11T00:00:00.000Z',
    });
    const trustPacket = {
      ...routeTrustPacket,
      signature: {
        algorithm: 'HMAC-SHA256',
        signer: 'control-plane-test-steward',
        signedAt: '2026-07-11T00:00:00.000Z',
        value: 'control-plane-test-signature',
      },
    };

    const response = await fetch(`${baseUrl}/router/evaluate`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        requestId: 'route-request-1',
        orgId: 'org-router-1',
        customerId: 'customer-router-1',
        actorId: 'router-x',
        trustPacket,
        routeEvaluation: {
          workItem: { id: 'work-router-1' },
          runtime: {},
          limits: {},
        },
        provenance: {
          originSystem: 'server-test',
          method: 'router-evaluate',
        },
      }),
    });

    expect(response.status).toBe(201);
    const body = (await response.json()) as {
      routeDecisionArtifact: {
        artifactId: string;
        requestId: string;
        trustPacket: { signature?: { value?: string } };
        governance: { result: string };
      };
      governanceDecision: { result: string; ledgerEntryId: string };
      record: { decisionId: string; replayReportId?: string | null };
    };

    expect(body.routeDecisionArtifact.artifactId).toBe('route-request-1');
    expect(['allowed', 'warning', 'blocked']).toContain(body.routeDecisionArtifact.governance.result);
    expect(body.routeDecisionArtifact.trustPacket.signature?.value).toBeTruthy();
    expect(body.routeDecisionArtifact.governance.result).toBe(body.governanceDecision.result);
    expect(body.record.decisionId).toBe('route-request-1');

    const decisionsResponse = await fetch(`${baseUrl}/router/decisions/route-request-1`);
    expect(decisionsResponse.status).toBe(200);
    const decisionsBody = (await decisionsResponse.json()) as { decisionId: string; artifact: { artifactId: string }; governanceDecision: { result: string } };
    expect(decisionsBody.decisionId).toBe('route-request-1');
    expect(decisionsBody.artifact.artifactId).toBe('route-request-1');
    expect(['allowed', 'warning', 'blocked']).toContain(decisionsBody.governanceDecision.result);
  });

  it('creates replay sessions and serves replay reports', async () => {
    const response = await fetch(`${baseUrl}/replay/sessions`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        mode: 'counterfactual',
        scope: 'global',
        configVersionUsed: 'v1.1.0',
        timeRange: {
          start: '2026-07-11T00:00:00.000Z',
          end: '2026-07-11T01:00:00.000Z',
        },
        relationshipIds: ['rel-router-org'],
        decisionIds: ['decision-1'],
      }),
    });

    expect(response.status).toBe(201);
    const body = (await response.json()) as { replayId: string; report: { summary: { decisionsChanged: number } } };
    expect(body.replayId).toBeTruthy();
    expect(body.report.summary.decisionsChanged).toBe(1);

    const report = await fetch(`${baseUrl}/replay/reports/${body.replayId}`);
    expect(report.status).toBe(200);
    const reportBody = (await report.json()) as { replayId: string; scope: string };
    expect(reportBody.replayId).toBe(body.replayId);
    expect(reportBody.scope).toBe('global');
  });

  it('exposes constitutional cockpit planes for events, drift, authority, memory, and replay', async () => {
    const eventsResponse = await fetch(`${baseUrl}/events`);
    expect(eventsResponse.status).toBe(200);
    const eventsBody = (await eventsResponse.json()) as { events: { id: string; type: string }[] };
    expect(eventsBody.events.length).toBeGreaterThan(0);
    expect(eventsBody.events.some((event) => event.type === 'replay')).toBe(true);

    const driftResponse = await fetch(`${baseUrl}/drift`);
    expect(driftResponse.status).toBe(200);
    const driftBody = (await driftResponse.json()) as { window: string; approvedRate: number; blockedRate: number; trend: string };
    expect(driftBody.window).toBe('last_30_days');
    expect(driftBody.approvedRate).toBeGreaterThanOrEqual(0);
    expect(driftBody.blockedRate).toBeGreaterThanOrEqual(0);

    const clausesResponse = await fetch(`${baseUrl}/clauses-heatmap`);
    expect(clausesResponse.status).toBe(200);
    const clausesBody = (await clausesResponse.json()) as { clauses: Record<string, number> };
    expect(Object.keys(clausesBody.clauses).length).toBeGreaterThan(0);

    const authorityResponse = await fetch(`${baseUrl}/authority-map`);
    expect(authorityResponse.status).toBe(200);
    const authorityBody = (await authorityResponse.json()) as { boundaries: { actor: string; resource: string }[] };
    expect(authorityBody.boundaries.length).toBeGreaterThan(0);

    const timelineResponse = await fetch(`${baseUrl}/replay/timeline`);
    expect(timelineResponse.status).toBe(200);
    const timelineBody = (await timelineResponse.json()) as { points: { commit: string }[] };
    expect(timelineBody.points.length).toBeGreaterThan(0);

    const snapshotResponse = await fetch(`${baseUrl}/replay/rel-router-org`);
    expect(snapshotResponse.status).toBe(200);
    const snapshotBody = (await snapshotResponse.json()) as { commit: string; events: { artifactId: string }[]; graph: { nodes: unknown[] } };
    expect(snapshotBody.commit).toBe('rel-router-org');
    expect(snapshotBody.events.some((event) => event.artifactId === 'rel-router-org')).toBe(true);
    expect(snapshotBody.graph.nodes.length).toBeGreaterThan(0);

    const memoryResponse = await fetch(`${baseUrl}/memory/narratives?topic=trust`);
    expect(memoryResponse.status).toBe(200);
    const memoryBody = (await memoryResponse.json()) as { narratives: { topic: string }[] };
    expect(memoryBody.narratives.some((narrative) => narrative.topic === 'trust')).toBe(true);

    const ledgerResponse = await fetch(`${baseUrl}/governance/change-ledger`);
    expect(ledgerResponse.status).toBe(200);
    const ledgerBody = (await ledgerResponse.json()) as { entries: { entryId: string }[] };
    expect(ledgerBody.entries.some((entry) => entry.entryId === 'entry-044')).toBe(true);

    const replayStateResponse = await fetch(`${baseUrl}/governance/replay-state?timestamp=2026-07-11T19:11:00.000Z`);
    expect(replayStateResponse.status).toBe(200);
    const replayStateBody = (await replayStateResponse.json()) as { profiles: string[]; authorityModes: string[] };
    expect(replayStateBody.profiles).toContain('profile:prod-critical-v3');
    expect(replayStateBody.authorityModes).toContain('COUNCIL');

    const knowledgeResponse = await fetch(`${baseUrl}/ugr/query?ugql=${encodeURIComponent('TRACE concept risk FROM lineage WITH INCLUDE worlds, docs, metrics LIMIT 12')}`);
    expect(knowledgeResponse.status).toBe(200);
    const knowledgeBody = (await knowledgeResponse.json()) as { results: { refId: string }[]; meta: { verb: string } };
    expect(knowledgeBody.meta.verb).toBe('TRACE');
    expect(knowledgeBody.results.some((result) => result.refId === 'concept:risk')).toBe(true);

    const crfResponse = await fetch(`${baseUrl}/crf/artifacts/crf:prod-critical-incident`);
    expect(crfResponse.status).toBe(200);
    const crfBody = (await crfResponse.json()) as { validation: { valid: boolean } };
    expect(crfBody.validation.valid).toBe(true);
  });

  it('returns trust artifacts and receipts for operator review', async () => {
    const response = await fetch(`${baseUrl}/trust/artifacts/rel-model-safety`);
    expect(response.status).toBe(200);
    const body = (await response.json()) as { artifact: { kind: string; relationshipId: string } };
    expect(body.artifact.kind).toBe('relationship');
    expect(body.artifact.relationshipId).toBe('rel-model-safety');

    const receipts = await fetch(`${baseUrl}/trust/artifacts/rel-model-safety/receipts`);
    expect(receipts.status).toBe(200);
    const receiptsBody = (await receipts.json()) as { receipts: unknown[] };
    expect(receiptsBody.receipts.length).toBeGreaterThan(0);
  });

  it('creates governed cori alpha uploads and serves the upload intelligence surface', async () => {
    const response = await fetch(`${baseUrl}/upload`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        repo_path: getCoriAlphaRepositoryRoot(),
        developer_id: 'tester',
        dropbox_path: '/team/incoming',
        mode: 'push',
      }),
    });

    expect(response.status).toBe(201);
    const upload = (await response.json()) as {
      status: string;
      decision_id: string;
      receipt_id: string;
      ledger_entry_id: string;
      dropbox_file: string;
      upload: { commit: string; decision: { result: string }; validation: { valid: boolean } };
      validation: { valid: boolean };
    };
    expect(upload.status).toBe('approved');
    expect(upload.decision_id).toContain('decision-');
    expect(upload.receipt_id).toContain('receipt-');
    expect(upload.ledger_entry_id).toContain('ledger-');
    expect(upload.dropbox_file).toContain('incoming/build-');
    expect(upload.upload.commit).toBeTruthy();
    expect(upload.upload.decision.result).toBe('approved');
    expect(upload.validation.valid).toBe(true);

    const uploads = await fetch(`${baseUrl}/uploads`);
    expect(uploads.status).toBe(200);
    const uploadsBody = (await uploads.json()) as { uploads: { commit: string }[]; summary: { uploadCount: number } };
    expect(uploadsBody.summary.uploadCount).toBeGreaterThan(0);
    expect(uploadsBody.uploads.some((entry) => entry.commit === upload.upload.commit)).toBe(true);

    const uploadDetail = await fetch(`${baseUrl}/upload/${upload.upload.commit}`);
    expect(uploadDetail.status).toBe(200);
    const uploadDetailBody = (await uploadDetail.json()) as { commit: string; evidence: { path: string } };
    expect(uploadDetailBody.commit).toBe(upload.upload.commit);
    expect(uploadDetailBody.evidence.path).toContain('evidence-');

    const graph = await fetch(`${baseUrl}/graph`);
    expect(graph.status).toBe(200);
    const graphBody = (await graph.json()) as { relationships: { type: string }[] };
    expect(graphBody.relationships.some((relationship) => relationship.type === 'governs')).toBe(true);

    const lineage = await fetch(`${baseUrl}/lineage/${upload.upload.commit}`);
    expect(lineage.status).toBe(200);
    const lineageBody = (await lineage.json()) as { lineage: string[] };
    expect(lineageBody.lineage.length).toBeGreaterThan(0);

    const stats = await fetch(`${baseUrl}/stats`);
    expect(stats.status).toBe(200);
    const statsBody = (await stats.json()) as { uploadCount: number; approvedCount: number };
    expect(statsBody.uploadCount).toBeGreaterThan(0);
    expect(statsBody.approvedCount).toBeGreaterThan(0);

    const validate = await fetch(`${baseUrl}/validate`);
    expect(validate.status).toBe(200);
    const validateBody = (await validate.json()) as { validation: { valid: boolean } };
    expect(validateBody.validation.valid).toBe(true);

    const dropboxValidate = await fetch(`${baseUrl}/dropbox/validate`, { method: 'POST' });
    expect(dropboxValidate.status).toBe(200);
    const dropboxValidateBody = (await dropboxValidate.json()) as { status: string; validation: { valid: boolean } };
    expect(dropboxValidateBody.status).toBe('pass');
    expect(dropboxValidateBody.validation.valid).toBe(true);
  }, 120000);
});
