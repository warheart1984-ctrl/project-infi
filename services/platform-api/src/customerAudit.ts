import { createHmac } from 'node:crypto';

import type { CustomerRecord } from '@aaes-os/platform-core';
import {
  buildRelationshipTrustPacket,
  calculateTrustView,
  trustPolicyForGovernanceLevel,
  type GovernanceTrustPolicy,
  type RelationshipLedgerTrustPacket,
  type RelationshipTrustView,
} from '@aaes-os/sovereignx-router';
import type { TreasuryPlan } from './treasury.js';

export interface CustomerQuotaSummary {
  requestLimit: number;
  requestCount: number;
  requestOverage: number;
  tokenLimit: number;
  tokenCount: number;
  tokenOverage: number;
  overageBillingUsd: number;
  overageBillingEnabled: boolean;
  enforcement: {
    status: 'within_limit' | 'metered_overage' | 'blocked';
    allowed: boolean;
    reason: string;
  };
}

export interface CustomerAuditSurface {
  customerId: string;
  organizationId?: string;
  organizationRole?: string;
  planId: string;
  planName: string;
  generatedAt: string;
  requestId: string;
  routingJustification: string;
  pricingJustification: string;
  entitlements: {
    routingTier: string;
    governanceLevel: string;
    auditScope: string;
    customerAuditSurfaces: boolean;
    overageBillingEnabled: boolean;
  };
  quota: CustomerQuotaSummary;
  treasury: {
    grossInvoiceUsd: number;
    openAiUsageCostUsd: number;
    taxReserveUsd: number;
    platformReserveUsd: number;
    ownerProfitUsd: number;
  };
  pricingPlan: {
    strategy: string;
    packaging: string;
    targetMarginBand: string;
  };
  routeDecisionArtifact?: unknown;
  trust: CustomerTrustSurface;
}

export interface CustomerTrustSurface {
  packet: RelationshipLedgerTrustPacket;
  signature: {
    algorithm: 'HMAC-SHA256';
    signer: string;
    signedAt: string;
    value: string;
  };
  policy: GovernanceTrustPolicy;
  allowed: boolean;
  reason: string;
}

export interface SignedCustomerAuditSurface {
  signer: string;
  signed_at: string;
  signature: string;
  surface: CustomerAuditSurface;
}

function canonicalizeSurface(surface: CustomerAuditSurface, signer: string, signedAt: string): string {
  return JSON.stringify({
    signer,
    signed_at: signedAt,
    surface,
  });
}

function canonicalizeJson(value: unknown): string {
  return JSON.stringify(sortValue(value));
}

function sortValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortValue);
  }
  if (!value || typeof value !== 'object') {
    return value;
  }
  const result: Record<string, unknown> = {};
  for (const key of Object.keys(value as Record<string, unknown>).sort()) {
    const entry = (value as Record<string, unknown>)[key];
    if (entry !== undefined) {
      result[key] = sortValue(entry);
    }
  }
  return result;
}

function signRelationshipTrustPacket(
  packet: RelationshipLedgerTrustPacket,
  secret: string,
  signer = 'platform-api',
  signedAt = new Date().toISOString(),
): { algorithm: 'HMAC-SHA256'; signer: string; signedAt: string; value: string } {
  const value = createHmac('sha256', secret).update(canonicalizeJson(packet)).digest('hex');
  return {
    algorithm: 'HMAC-SHA256',
    signer,
    signedAt,
    value,
  };
}

export function signCustomerAuditSurface(
  surface: CustomerAuditSurface,
  secret: string,
  signer = 'platform-api',
  signedAt = new Date().toISOString(),
): SignedCustomerAuditSurface {
  const payload = canonicalizeSurface(surface, signer, signedAt);
  const signature = createHmac('sha256', secret).update(payload).digest('hex');
  return {
    signer,
    signed_at: signedAt,
    signature,
    surface,
  };
}

export function verifySignedCustomerAuditSurface(
  signed: SignedCustomerAuditSurface,
  secret: string,
): boolean {
  const expected = signCustomerAuditSurface(signed.surface, secret, signed.signer, signed.signed_at).signature;
  return expected === signed.signature;
}

export function buildCustomerAuditSurface(input: {
  customer: CustomerRecord;
  requestId: string;
  routingJustification: string;
  pricingJustification: string;
  quota: CustomerQuotaSummary;
  treasuryPlan: TreasuryPlan;
  strategy: string;
  packaging: string;
  targetMarginBand: string;
  routeDecisionArtifact?: unknown;
  trust?: CustomerTrustSurface;
}): CustomerAuditSurface {
  const trust = input.trust ?? buildRelationshipTrustSurface({
    customer: input.customer,
    requestId: input.requestId,
  });

  return {
    customerId: input.customer.id,
    organizationId: input.customer.organizationId,
    organizationRole: input.customer.organizationRole,
    planId: input.customer.planId,
    planName: input.customer.planName,
    generatedAt: new Date().toISOString(),
    requestId: input.requestId,
    routingJustification: input.routingJustification,
    pricingJustification: input.pricingJustification,
    entitlements: {
      routingTier: input.customer.entitlements.routingTier,
      governanceLevel: input.customer.entitlements.governanceLevel,
      auditScope: input.customer.entitlements.auditScope,
      customerAuditSurfaces: input.customer.entitlements.customerAuditSurfaces,
      overageBillingEnabled: input.customer.entitlements.overageBillingEnabled,
    },
    quota: input.quota,
    treasury: {
      grossInvoiceUsd: input.treasuryPlan.grossInvoiceUsd,
      openAiUsageCostUsd: input.treasuryPlan.openAiUsageCostUsd,
      taxReserveUsd: input.treasuryPlan.taxReserveUsd,
      platformReserveUsd: input.treasuryPlan.platformReserveUsd,
      ownerProfitUsd: input.treasuryPlan.ownerProfitUsd,
    },
    pricingPlan: {
      strategy: input.strategy,
      packaging: input.packaging,
      targetMarginBand: input.targetMarginBand,
    },
    routeDecisionArtifact: input.routeDecisionArtifact,
    trust,
  };
}

export function buildRelationshipTrustSurface(input: {
  customer: CustomerRecord;
  requestId: string;
  signingSecret?: string;
}): CustomerTrustSurface {
  const governanceLevel = input.customer.entitlements.governanceLevel;
  const policy = trustPolicyForGovernanceLevel(governanceLevel);
  const capturedAt = new Date().toISOString();
  const evidenceIds = [
    `customer:${input.customer.id}`,
    input.customer.organizationId ? `organization:${input.customer.organizationId}` : `owner:${input.customer.ownerId}`,
    input.customer.organizationRole ? `role:${input.customer.organizationRole}` : 'role:unassigned',
  ];

  const authorityLevel = authorityLevelForCustomer(input.customer);
  const evidenceStrength = evidenceStrengthForCustomer(input.customer);
  const confidence = confidenceForCustomer(input.customer);
  const trustView: RelationshipTrustView = calculateTrustView(confidence, authorityLevel, evidenceStrength);
  trustView.evidenceIds = evidenceIds;
  trustView.authority = {
    stewardId: input.customer.organizationRole ? input.customer.id : input.customer.ownerId,
    delegationChainIds: input.customer.organizationId ? [input.customer.organizationId] : [input.customer.ownerId],
  };
  trustView.provenance = {
    originSystem: 'platform-api/relationship-ledger',
    originActorId: input.customer.id,
    method: input.customer.organizationId ? 'organization-membership' : 'identity-registration',
    createdAt: new Date().toISOString(),
    standardsTraceabilityIds: ['cis.relationship.intelligence', 'cis.trust.ledger'],
  };

  const packet = buildRelationshipTrustPacket({
    relationshipId: buildRelationshipId(input.customer),
    revision: 1,
    subjectId: input.customer.id,
    objectId: input.customer.organizationId ?? input.customer.ownerId,
    relationshipKind: input.customer.organizationId ? 'membership' : 'identity',
    governanceLevel,
    authorityChain: input.customer.organizationId ? [input.customer.organizationId, input.customer.ownerId] : [input.customer.ownerId],
    trust: trustView,
    ledgerEntryId: `ledger-${input.requestId}`,
    receiptId: `receipt-${input.requestId}`,
    capturedAt,
  });
  const signature = signRelationshipTrustPacket(packet, input.signingSecret ?? process.env.TRUST_PACKET_SIGNING_SECRET ?? 'platform-api-trust', 'platform-api', capturedAt);
  packet.signature = signature;

  const allowed = trustView.score >= policy.minTrustScore && (!policy.minTrustBand || bandRank(trustView.band) >= bandRank(policy.minTrustBand));
  const reason = allowed
    ? `trust ${trustView.band} satisfies ${policy.governanceLevel} governance thresholds`
    : `trust ${trustView.band} does not satisfy ${policy.governanceLevel} governance thresholds`;

  return {
    packet,
    signature,
    policy,
    allowed,
    reason,
  };
}

function buildRelationshipId(customer: CustomerRecord): string {
  return customer.organizationId
    ? `rel:${customer.organizationId}:${customer.id}`
    : `rel:${customer.ownerId}:${customer.id}`;
}

function confidenceForCustomer(customer: CustomerRecord): number {
  if (customer.organizationRole === 'owner') return 0.96;
  if (customer.organizationRole === 'admin') return 0.9;
  if (customer.organizationRole === 'auditor') return 0.86;
  if (customer.organizationRole === 'analyst') return 0.8;
  if (customer.organizationRole === 'developer') return 0.76;
  return customer.organizationId ? 0.72 : 0.58;
}

function authorityLevelForCustomer(customer: CustomerRecord): number {
  if (customer.organizationRole === 'owner') return 0.98;
  if (customer.organizationRole === 'admin') return 0.88;
  if (customer.organizationRole === 'auditor') return 0.82;
  if (customer.organizationRole === 'analyst') return 0.78;
  if (customer.organizationRole === 'developer') return 0.72;
  return customer.organizationId ? 0.68 : 0.55;
}

function evidenceStrengthForCustomer(customer: CustomerRecord): number {
  if (customer.organizationId && customer.entitlements.auditScope === 'org') return 0.94;
  if (customer.organizationId && customer.entitlements.auditScope === 'team') return 0.88;
  if (customer.organizationId) return 0.83;
  return 0.68;
}

function bandRank(band: RelationshipTrustView['band']): number {
  switch (band) {
    case 'low':
      return 0;
    case 'medium':
      return 1;
    case 'high':
      return 2;
  }
  return 0;
}
