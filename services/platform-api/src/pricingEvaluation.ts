import {
  evaluateSovereignRouterXPricing,
  buildRouteDecisionArtifact,
  type SovereignRouterXPricingEvaluation,
  type SovereignRouterXPricingInput,
} from '@aaes-os/sovereignx-router';
import type { CustomerEntitlements, CustomerRecord, UsageRecord } from '@aaes-os/platform-core';

import { createTreasuryPlan, type TreasuryPlan } from './treasury.js';
import type { CodexReplyPacket, SignedCodexReplyPacket } from './codexReply.js';
import { signCodexReplyPacket } from './codexReply.js';
import {
  buildCustomerAuditSurface,
  buildRelationshipTrustSurface,
  signCustomerAuditSurface,
  type CustomerAuditSurface,
  type CustomerQuotaSummary,
  type SignedCustomerAuditSurface,
} from './customerAudit.js';

export interface PricingEvaluationBundle {
  evaluation: SovereignRouterXPricingEvaluation;
  routeDecisionArtifact: ReturnType<typeof buildRouteDecisionArtifact>;
  treasuryPlan: TreasuryPlan;
  reply: CodexReplyPacket;
  signedReply: SignedCodexReplyPacket | null;
  auditSurface: CustomerAuditSurface;
  signedAuditSurface: SignedCustomerAuditSurface | null;
  quota: CustomerQuotaSummary;
  usageRecord: Omit<UsageRecord, 'id' | 'timestamp'>;
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function numberOr(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

export function buildPricingEvaluationBundle(input: {
  ownerId: string;
  customerId: string;
  customer?: CustomerRecord;
  customerEntitlements: CustomerEntitlements;
  governanceProfile: import('@aaes-os/platform-core').GovernanceMode;
  trustSurface?: ReturnType<typeof buildRelationshipTrustSurface>;
  usageRecords?: UsageRecord[];
  pricing: Partial<SovereignRouterXPricingInput> & Pick<SovereignRouterXPricingInput, 'segment'> & {
    customerInvoiceUsd?: number;
  };
  openAiUsageCostUsd?: number;
  taxRatePct?: number;
  profitReservePct?: number;
  platformReservePct?: number;
  signingSecret?: string;
  routeDecisionSigningSecret?: string;
}): PricingEvaluationBundle {
  const requestId = `pricing-${Date.now().toString(36)}`;
  const customer =
    input.customer ?? {
      id: input.customerId,
      ownerId: input.ownerId,
      email: `${input.customerId}@example.com`,
      authProvider: 'email',
      planId: 'pro',
      planName: 'Pro',
      entitlements: input.customerEntitlements,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  const trustSurface = input.trustSurface ?? buildRelationshipTrustSurface({
    customer,
    requestId,
  });
  const evaluation = evaluateSovereignRouterXPricing({
    segment: input.pricing.segment,
    monthlyCustomers: numberOr(input.pricing.monthlyCustomers, 1),
    routedRequestsPerCustomer: numberOr(input.pricing.routedRequestsPerCustomer, 120),
    governanceReviewsPerCustomer: numberOr(input.pricing.governanceReviewsPerCustomer, 2),
    knowledgeUpdatesPerCustomer: numberOr(input.pricing.knowledgeUpdatesPerCustomer, 4),
    serviceHoursPerCustomer: numberOr(input.pricing.serviceHoursPerCustomer, 0),
    compliancePressure: numberOr(input.pricing.compliancePressure, 35),
    workloadVolatility: numberOr(input.pricing.workloadVolatility, 45),
    supportComplexity: numberOr(input.pricing.supportComplexity, 35),
    privateDeployment: input.pricing.privateDeployment ?? false,
    assuranceRequired: input.pricing.assuranceRequired ?? false,
    governanceLevel: trustSurface.policy.governanceLevel,
    trust: trustSurface.packet.trust,
  }, {
    requestId,
  });
  const routeDecisionArtifact = buildRouteDecisionArtifact({
    artifactId: requestId,
    requestId,
    orgId: customer.organizationId ?? input.ownerId,
    customerId: input.customerId,
    relationshipId: trustSurface.packet.relationshipId,
    trustPacket: trustSurface.packet,
    trustPolicy: trustSurface.policy,
    routeEvaluation: evaluation.routing.routeEvaluation,
    provenance: {
      originSystem: 'platform-api/pricing-evaluation',
      originActorId: customer.id,
      method: 'pricing-evaluation',
      standardsTraceabilityIds: ['cis.routing.decision', 'cis.trust.ledger'],
    },
    decidedBy: 'platform-api',
    signingSecret: input.routeDecisionSigningSecret ?? process.env.ROUTE_DECISION_SIGNING_SECRET ?? 'platform-api-route-decision',
    signer: 'platform-api',
  });

  const previousRecords = input.usageRecords ?? [];
  const currentEstimatedTokens = Math.ceil(
    numberOr(input.pricing.routedRequestsPerCustomer, 120) * numberOr(input.pricing.monthlyCustomers, 1) * 80,
  );
  const previousRequests = previousRecords.filter((record) => record.operation === 'billing:pricing-evaluate').length;
  const previousTokens = previousRecords.reduce((sum, record) => {
    const tokens = typeof record.metadata?.estimatedTokens === 'number' && Number.isFinite(record.metadata.estimatedTokens)
      ? record.metadata.estimatedTokens
      : record.units * 250;
    return sum + tokens;
  }, 0);
  const requestCount = previousRequests + 1;
  const requestOverage = Math.max(0, requestCount - input.customerEntitlements.maxRequestsPerMonth);
  const tokenCount = previousTokens + currentEstimatedTokens;
  const tokenOverage = Math.max(0, tokenCount - input.customerEntitlements.maxTokensPerMonth);
  const overageBillingUsd = round(
    (requestOverage * 0.45) + (tokenOverage * 0.0000125),
  );
  const quota: CustomerQuotaSummary = {
    requestLimit: input.customerEntitlements.maxRequestsPerMonth,
    requestCount,
    requestOverage,
    tokenLimit: input.customerEntitlements.maxTokensPerMonth,
    tokenCount,
    tokenOverage,
    overageBillingUsd,
    overageBillingEnabled: input.customerEntitlements.overageBillingEnabled,
    enforcement: {
      status:
        requestOverage > 0 || tokenOverage > 0
          ? input.customerEntitlements.overageBillingEnabled
            ? 'metered_overage'
            : 'blocked'
          : 'within_limit',
      allowed: input.customerEntitlements.overageBillingEnabled || (requestOverage === 0 && tokenOverage === 0),
      reason:
        requestOverage > 0 || tokenOverage > 0
          ? input.customerEntitlements.overageBillingEnabled
            ? 'Overage billed against the entitlement'
            : 'Overage blocked because billing is disabled for this entitlement'
          : 'Within entitlement limits',
    },
  };

  const treasuryPlan = createTreasuryPlan(
    {
      customerId: input.customerId,
      ownerId: input.ownerId,
      governanceProfile: input.governanceProfile,
      customerInvoiceUsd: round(numberOr(input.pricing.customerInvoiceUsd, evaluation.economics.monthlyRevenueUsd) + overageBillingUsd),
      openAiUsageCostUsd: round(numberOr(input.openAiUsageCostUsd, evaluation.economics.monthlyDirectCostUsd * 0.38)),
      taxRatePct: numberOr(input.taxRatePct, 22),
      profitReservePct: numberOr(input.profitReservePct, 18),
      platformReservePct: numberOr(input.platformReservePct, 8),
    },
    [],
  );

  const targetMarginBand = evaluation.recommendedScenario.estimatedGrossMarginPct >= 80
    ? '80-90%'
    : evaluation.recommendedScenario.estimatedGrossMarginPct >= 60
      ? '60-80%'
      : '40-60%';

  const reply: CodexReplyPacket = {
    status: 'done',
    summary: `Pricing evaluation completed for ${input.pricing.segment}; ${evaluation.recommendedScenario.strategy} was selected and the treasury plan separated OpenAI, tax, and owner-profit reserves.`,
    changed_files: [
      'services/platform-api/src/routes.ts',
      'services/platform-web/app/pricing/PricingEvaluatorClient.tsx',
    ],
    verification: [
      'customer-authenticated pricing evaluation completed',
      'treasury plan computed',
      'codex handoff packet produced',
    ],
    next_action: 'Review the returned pricing recommendation, treasury plan, and signed reply packet.',
    blockers: [],
  };

  const signedReply = input.signingSecret ? signCodexReplyPacket(reply, input.signingSecret, 'platform-api') : null;
  const auditSurface = buildCustomerAuditSurface({
    customer,
    requestId,
    routingJustification: `Routing via ${evaluation.recommendedScenario.strategy} for ${evaluation.input.segment}.`,
    pricingJustification: `Selected ${evaluation.recommendedScenario.strategy} for ${evaluation.input.segment} with estimated margin ${evaluation.economics.grossMarginPct.toFixed(1)}%.`,
    quota,
    treasuryPlan,
    strategy: evaluation.recommendedScenario.strategy,
    packaging: evaluation.recommendedScenario.packaging,
    targetMarginBand,
    trust: trustSurface,
    routeDecisionArtifact,
  });
  const signedAuditSurface = input.signingSecret
    ? signCustomerAuditSurface(auditSurface, input.signingSecret, 'platform-api')
    : null;

  const usageRecord: Omit<UsageRecord, 'id' | 'timestamp'> = {
    ownerId: input.ownerId,
    orgId: customer.organizationId,
    customerId: input.customerId,
    capabilityId: 'billing:pricing-evaluate',
    operation: 'billing:pricing-evaluate',
    units: Math.max(1, Math.ceil(evaluation.economics.routedRequests / 4)),
    governanceProfile: input.governanceProfile,
      metadata: {
        segment: evaluation.input.segment,
        strategy: evaluation.recommendedScenario.strategy,
        revenueUsd: evaluation.economics.monthlyRevenueUsd,
        marginPct: evaluation.economics.grossMarginPct,
        estimatedTokens: currentEstimatedTokens,
        requestCount,
        organizationId: customer.organizationId,
        trustRelationshipId: trustSurface.packet.relationshipId,
        trustPolicy: trustSurface.policy.governanceLevel,
        routeDecisionArtifact,
      },
    };

  return {
    evaluation,
    routeDecisionArtifact,
    treasuryPlan,
    reply,
    signedReply,
    auditSurface,
    signedAuditSurface,
    quota,
    usageRecord,
  };
}
