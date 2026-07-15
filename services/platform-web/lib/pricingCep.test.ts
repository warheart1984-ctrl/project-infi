import { generateKeyPairSync } from 'node:crypto';

import { describe, expect, it, vi } from 'vitest';

import { buildPricingEvaluationCepBundle, publishPricingEvaluationCepArtifacts } from './pricingCep';

describe('pricing CEP publication', () => {
  it('builds a three-artifact CEP bundle from a customer pricing evaluation', async () => {
    const context = {
      sessionId: 'sess_abc123',
      customerId: 'cust_123',
      customerPlanId: 'pro',
      customerPlanName: 'Pro',
      segment: 'Enterprise',
      requestBody: { segment: 'Enterprise', customerInvoiceUsd: 500 },
      responseBody: {
        evaluation: {
          requestId: 'pricing-request-1',
          recommendedScenario: {
            strategy: 'Enterprise bundle',
            packaging: 'Bundle',
          },
          routing: {
            modelDecision: { model: 'qwen-7b' },
            backend: 'balanced-router',
          },
          economics: {
            grossMarginPct: 82.4,
          },
          requestPacket: {
            objective: 'Customer-authenticated pricing evaluation',
          },
        },
        treasuryPlan: { grossInvoiceUsd: 500 },
        reply: { status: 'done' },
        signedReply: { signer: 'platform-api' },
        auditSurface: {
          surface: {
            requestId: 'audit-request-1',
            planId: 'pro',
            planName: 'Pro',
            pricingJustification: 'Plan Pro supports the request volume.',
            routingJustification: 'Balanced router selected qwen-7b.',
            trust: {
              relationshipId: 'rel-org-cust-1',
              revision: 1,
              governanceLevel: 'enhanced',
              authorityChain: ['org-1', 'cust-123'],
              trust: {
                score: 0.82,
                band: 'high',
                evidenceIds: ['evidence-1'],
              },
            },
          },
        },
        quota: { requestLimit: 5000 },
        ledger: { persisted: true },
      },
    };

    const bundle = buildPricingEvaluationCepBundle(context, { auditSigningKeys: null });

    const typedBundle = bundle as {
      promotionRequest: { kind: string };
      replayJob: { kind: string };
      decision: { kind: string };
    };

    expect(typedBundle.promotionRequest.kind).toBe('promotion-request');
    expect(typedBundle.replayJob.kind).toBe('replay-job');
    expect(typedBundle.decision.kind).toBe('decision');
    expect(bundle.promotionRequestMetadata?.title).toContain('promotion request');
    expect(bundle.replayJobMetadata?.title).toContain('replay job');
    expect(bundle.decisionMetadata?.title).toContain('decision');
    expect((bundle.decision as { decision?: { selectedModel?: string } }).decision?.selectedModel).toBe('qwen-7b');
    expect((bundle.promotionRequest as { requestId?: string }).requestId).toBe('audit-request-1');
    expect((bundle.promotionRequest as { trust?: { relationshipId?: string } }).trust?.relationshipId).toBe('rel-org-cust-1');
    expect((bundle.decision as { trust?: { relationshipId?: string } }).trust?.relationshipId).toBe('rel-org-cust-1');

    const syncBundle = vi.fn(async () => ({
      promotionRequest: { id: 'cep-promo-1' },
      replayJob: { id: 'cep-replay-1' },
      decision: { id: 'cep-decision-1' },
      viewState: {
        selectedKind: 'decision' as const,
        selectedArtifactId: 'cep-decision-1',
        updatedAt: '2026-07-11T05:00:00.000Z',
        source: 'remote' as const,
      },
    }));
    const client = { syncBundle } as unknown as Parameters<typeof publishPricingEvaluationCepArtifacts>[1];

    const publication = await publishPricingEvaluationCepArtifacts(context, client, {}, { auditSigningKeys: null });

    expect(syncBundle).toHaveBeenCalledTimes(1);
    expect(publication.promotionRequest.id).toBe('cep-promo-1');
    expect(publication.replayJob.id).toBe('cep-replay-1');
    expect(publication.decision.id).toBe('cep-decision-1');
    expect(publication.viewState.selectedArtifactId).toBe('cep-decision-1');
  });

  it('emits a signed canonical audit packet when audit signing keys are provided', () => {
    const { privateKey, publicKey } = generateKeyPairSync('ed25519');
    const privateKeyPem = privateKey.export({ format: 'pem', type: 'pkcs8' }).toString();
    const publicKeyPem = publicKey.export({ format: 'pem', type: 'spki' }).toString();

    const context = {
      sessionId: 'sess_signed',
      customerId: 'cust_signed',
      customerPlanId: 'enterprise',
      customerPlanName: 'Enterprise',
      organizationId: 'org_signed',
      segment: 'Enterprise',
      requestBody: { segment: 'Enterprise' },
      responseBody: {
        evaluation: {
          requestId: 'pricing-request-signed',
          recommendedScenario: {
            strategy: 'Enterprise bundle',
            packaging: 'Bundle',
          },
          routing: {
            modelDecision: { model: 'qwen-7b' },
            backend: 'balanced-router',
          },
          economics: {
            grossMarginPct: 84.2,
          },
          requestPacket: {
            objective: 'Customer-authenticated pricing evaluation',
          },
        },
        treasuryPlan: { grossInvoiceUsd: 500 },
        reply: { status: 'done' },
        signedReply: { signer: 'platform-api' },
        auditSurface: {
          surface: {
            requestId: 'audit-request-signed',
            planId: 'enterprise',
            planName: 'Enterprise',
            pricingJustification: 'Enterprise bundle selected.',
            routingJustification: 'Balanced router selected qwen-7b.',
            trust: {
              relationshipId: 'rel-org-cust-signed',
              revision: 1,
              governanceLevel: 'full',
              authorityChain: ['org-signed', 'cust_signed'],
              trust: {
                score: 0.94,
                band: 'high',
                evidenceIds: ['evidence-signed'],
              },
            },
          },
        },
        quota: { requestLimit: 5000 },
        ledger: { persisted: true },
      },
    };

    const bundle = buildPricingEvaluationCepBundle(context, {
      auditSigningKeys: {
        privateKeyPem,
        publicKeyPem,
      },
    });

    expect((bundle.decision as { signature?: { algorithm: string; value: string } }).signature?.algorithm).toBe('Ed25519');
    expect((bundle.decision as { signature?: { algorithm: string; value: string } }).signature?.value).toBeTruthy();
    expect((bundle.decision as { decision?: { modelId?: string } }).decision?.modelId).toBe('qwen-7b');
    expect((bundle.decision as { input?: { context?: { trust?: { relationshipId?: string } } } }).input?.context?.trust?.relationshipId).toBe('rel-org-cust-signed');
    expect((bundle.decision as { governance?: { trustPolicy?: { governanceLevel?: string } } }).governance?.trustPolicy?.governanceLevel).toBe('full');
  });
});
