import {
  CepOrchestratorClient,
  type CepArtifactMetadata,
  type CepOrchestratorBundle,
  type CepOrchestratorClientOptions,
} from './cepOrchestratorClient';
import {
  readAuditSigningKeysFromEnv,
  signCanonicalAuditPacket,
  type AuditSigningKeys,
  type CanonicalAuditPacketInput,
  validateAuditPacket,
  validateUnsignedAuditPacket,
} from '@aaes-os/platform-core';

export interface PricingEvaluationCepContext {
  sessionId: string;
  customerId: string;
  customerPlanId: string;
  customerPlanName: string;
  organizationId?: string;
  segment: string;
  trustSurface?: unknown;
  requestBody: Record<string, unknown>;
  responseBody: {
    evaluation?: {
      requestId?: string;
      recommendedScenario?: {
        strategy?: string;
        packaging?: string;
      };
      routing?: {
        modelDecision?: { model?: string };
        backend?: string;
      };
      economics?: Record<string, unknown>;
      requestPacket?: Record<string, unknown>;
    };
    treasuryPlan?: unknown;
    reply?: unknown;
    signedReply?: unknown;
    auditSurface?: {
      surface?: {
        requestId?: string;
        planId?: string;
        planName?: string;
        quota?: Record<string, unknown>;
        pricingJustification?: string;
        routingJustification?: string;
        trust?: unknown;
        routeDecisionArtifact?: unknown;
      };
    };
    quota?: Record<string, unknown>;
    ledger?: Record<string, unknown>;
    routeDecisionArtifact?: unknown;
  };
}

export interface PricingEvaluationCepPublication {
  promotionRequest: Awaited<ReturnType<CepOrchestratorClient['postPromotionRequest']>>;
  replayJob: Awaited<ReturnType<CepOrchestratorClient['postReplayJob']>>;
  decision: Awaited<ReturnType<CepOrchestratorClient['postDecision']>>;
  viewState: Awaited<ReturnType<CepOrchestratorClient['setViewState']>>['viewState'];
}

export function buildPricingEvaluationCepBundle(
  context: PricingEvaluationCepContext,
  options: { auditSigningKeys?: AuditSigningKeys | null } = {},
): CepOrchestratorBundle {
  const requestId =
    context.responseBody.auditSurface?.surface?.requestId ??
    context.responseBody.evaluation?.requestId ??
    `pricing-${context.sessionId}`;
  const recommendation = context.responseBody.evaluation?.recommendedScenario ?? {};
  const routing = context.responseBody.evaluation?.routing ?? {};
  const economics = context.responseBody.evaluation?.economics ?? {};
  const requestPacket = context.responseBody.evaluation?.requestPacket ?? {};
  const surface = (context.responseBody.auditSurface?.surface ?? {}) as {
    trust?: unknown;
    routingJustification?: string;
    pricingJustification?: string;
    requestId?: string;
  };
  const trust = surface.trust ?? context.trustSurface ?? null;
  const routeDecisionArtifact = context.responseBody.routeDecisionArtifact ?? context.responseBody.auditSurface?.surface?.routeDecisionArtifact ?? null;

  const basePayload = {
    requestId,
    sessionId: context.sessionId,
    customerId: context.customerId,
    organizationId: context.organizationId ?? null,
    customerPlanId: context.customerPlanId,
    customerPlanName: context.customerPlanName,
    segment: context.segment,
    requestBody: context.requestBody,
    requestPacket,
    recommendation,
    routing,
    economics,
    treasuryPlan: context.responseBody.treasuryPlan ?? null,
    reply: context.responseBody.reply ?? null,
    signedReply: context.responseBody.signedReply ?? null,
    auditSurface: context.responseBody.auditSurface ?? null,
    trust,
    routeDecisionArtifact,
    quota: context.responseBody.quota ?? null,
    ledger: context.responseBody.ledger ?? null,
  };

  const promotionMetadata: CepArtifactMetadata = {
    title: `Pricing evaluation promotion request for ${context.segment}`,
    source: 'platform-web/pricing-evaluate',
    organizationId: context.organizationId,
    id: `pricing-promo-${context.sessionId}`,
  };

  const replayMetadata: CepArtifactMetadata = {
    title: `Pricing evaluation replay job for ${context.segment}`,
    source: 'platform-web/pricing-evaluate',
    organizationId: context.organizationId,
    id: `pricing-replay-${context.sessionId}`,
  };

  const decisionMetadata: CepArtifactMetadata = {
    title: `Pricing evaluation decision for ${context.segment}`,
    source: 'platform-web/pricing-evaluate',
    organizationId: context.organizationId,
    id: `pricing-decision-${context.sessionId}`,
  };

  const auditKeys =
    options.auditSigningKeys === undefined ? readAuditSigningKeysFromEnv() : options.auditSigningKeys;
  const legacyDecision = {
    ...basePayload,
    kind: 'decision',
    stage: 'decision',
    decision: {
      status: 'APPROVED',
      strategy: recommendation.strategy ?? 'Unknown',
      packaging: recommendation.packaging ?? 'Unknown',
      selectedModel: routing.modelDecision?.model ?? 'unknown',
      backend: routing.backend ?? 'unknown',
    },
    pricingPlan: {
      strategy: recommendation.strategy ?? 'Unknown',
      packaging: recommendation.packaging ?? 'Unknown',
    },
  };

  const signedDecision = auditKeys
    ? buildSignedCanonicalDecisionPacket({
        requestId,
        context,
        recommendation,
        routing,
        economics,
        requestPacket,
        surface,
        auditKeys,
      })
    : null;

  const decision = signedDecision ?? legacyDecision;

  if (signedDecision) {
    decisionMetadata.signature = signedDecision.signature.value;
  }

  return {
    promotionRequest: {
      ...basePayload,
      kind: 'promotion-request',
      stage: 'promotion-request',
      summary: `Customer-authenticated pricing evaluation for ${context.segment}`,
      routingJustification: surface.routingJustification ?? null,
      pricingJustification: surface.pricingJustification ?? null,
      trust,
    },
    replayJob: {
      ...basePayload,
      kind: 'replay-job',
      stage: 'replay-job',
      replayWindow: {
        start: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        end: new Date().toISOString(),
      },
      replayInputs: {
        requestId,
        signedReply: context.responseBody.signedReply ?? null,
        reply: context.responseBody.reply ?? null,
        auditSurface: context.responseBody.auditSurface ?? null,
        trust,
      },
    },
    decision,
    promotionRequestMetadata: promotionMetadata,
    replayJobMetadata: replayMetadata,
    decisionMetadata: decisionMetadata,
  };
}

export async function publishPricingEvaluationCepArtifacts(
  context: PricingEvaluationCepContext,
  client?: CepOrchestratorClient,
  clientOptions: CepOrchestratorClientOptions = {},
  options: { auditSigningKeys?: AuditSigningKeys | null } = {},
): Promise<PricingEvaluationCepPublication> {
  const orchestrator =
    client ??
    new CepOrchestratorClient({
      baseUrl: clientOptions.baseUrl,
      fetchImpl: clientOptions.fetchImpl,
    });

  const bundle = buildPricingEvaluationCepBundle(context, options);
  const publication = await orchestrator.syncBundle({
    promotionRequest: bundle.promotionRequest,
    replayJob: bundle.replayJob,
    decision: bundle.decision,
    promotionRequestMetadata: bundle.promotionRequestMetadata,
    replayJobMetadata: bundle.replayJobMetadata,
    decisionMetadata: bundle.decisionMetadata,
  });

  return publication;
}

function buildSignedCanonicalDecisionPacket(input: {
  requestId: string;
  context: PricingEvaluationCepContext;
  recommendation: { strategy?: string; packaging?: string };
  routing: { modelDecision?: { model?: string }; backend?: string };
  economics: Record<string, unknown>;
  requestPacket: Record<string, unknown>;
  surface: NonNullable<PricingEvaluationCepContext['responseBody']['auditSurface']>['surface'];
  auditKeys: AuditSigningKeys;
}): ReturnType<typeof signCanonicalAuditPacket> {
  const governanceLevel = input.context.customerPlanId === 'enterprise' ? 'full' : input.context.customerPlanId === 'pro' ? 'enhanced' : 'basic';
  const surface = (input.surface ?? {}) as {
    trust?: unknown;
    routingJustification?: string;
    pricingJustification?: string;
  };
  const packet: CanonicalAuditPacketInput = {
    version: '1.0',
    packetId: `audit-${input.requestId}`,
    orgId: input.context.organizationId ?? input.context.customerId,
    customerId: input.context.customerId,
    requestId: input.requestId,
    createdAt: new Date().toISOString(),
    domain: 'pricing',
    input: {
      context: {
        sessionId: input.context.sessionId,
        customerId: input.context.customerId,
        customerPlanId: input.context.customerPlanId,
        customerPlanName: input.context.customerPlanName,
        segment: input.context.segment,
        requestBody: input.context.requestBody,
        requestPacket: input.requestPacket,
        recommendation: input.recommendation,
        routing: input.routing,
        economics: input.economics,
        auditSurface: input.context.responseBody.auditSurface ?? null,
        trust: surface.trust ?? null,
        routeDecisionArtifact: input.context.responseBody.routeDecisionArtifact ?? null,
        quota: input.context.responseBody.quota ?? null,
        ledger: input.context.responseBody.ledger ?? null,
        treasuryPlan: input.context.responseBody.treasuryPlan ?? null,
        reply: input.context.responseBody.reply ?? null,
        signedReply: input.context.responseBody.signedReply ?? null,
      },
    },
    policy: {
      id: `pricing-policy-${input.context.customerPlanId}`,
      name: `${input.context.customerPlanName} pricing policy`,
      dsl: [
        `require plan.id = ${input.context.customerPlanId}`,
        `require segment = ${input.context.segment}`,
        `prefer strategy = ${input.recommendation.strategy ?? 'Unknown'}`,
        `prefer packaging = ${input.recommendation.packaging ?? 'Unknown'}`,
        `prefer model = ${input.routing.modelDecision?.model ?? 'unknown'}`,
        `prefer backend = ${input.routing.backend ?? 'unknown'}`,
      ].join('\n'),
      compiledConstraints: {
        recommendation: input.recommendation,
        routing: input.routing,
        economics: input.economics,
        requestPacket: input.requestPacket,
        auditSurface: surface,
        trust: surface.trust ?? null,
      },
    },
    decision: {
      modelId: input.routing.modelDecision?.model ?? 'unknown',
      outcome: {
        status: 'APPROVED',
        strategy: input.recommendation.strategy ?? 'Unknown',
        packaging: input.recommendation.packaging ?? 'Unknown',
        selectedModel: input.routing.modelDecision?.model ?? 'unknown',
        backend: input.routing.backend ?? 'unknown',
        auditSurface: surface,
        trust: surface.trust ?? null,
      },
      scores: input.economics,
    },
    governance: {
      level: governanceLevel,
      conformanceStatus: 'passing',
      driftRisk: 'low',
      lineageDepth: 1,
      trustPolicy: {
        governanceLevel,
        minTrustScore: input.context.customerPlanId === 'enterprise' ? 0.75 : input.context.customerPlanId === 'pro' ? 0.55 : 0.2,
        minTrustBand: input.context.customerPlanId === 'enterprise' ? 'high' : input.context.customerPlanId === 'pro' ? 'medium' : 'low',
      },
    },
    treasury: {
      price: extractGrossInvoiceUsd(input.context.responseBody.treasuryPlan),
      currency: 'USD',
      reserves: input.context.responseBody.treasuryPlan ?? null,
    },
  };

  validateUnsignedAuditPacket(packet);
  const signedPacket = signCanonicalAuditPacket(packet, input.auditKeys.privateKeyPem);
  validateAuditPacket(signedPacket);
  return signedPacket;
}

function extractGrossInvoiceUsd(treasuryPlan: unknown): number | undefined {
  if (!treasuryPlan || typeof treasuryPlan !== 'object') {
    return undefined;
  }
  const plan = treasuryPlan as { grossInvoiceUsd?: unknown };
  return typeof plan.grossInvoiceUsd === 'number' ? plan.grossInvoiceUsd : undefined;
}
