export type CanonicalAuditDomain = 'pricing' | 'routing' | 'entitlements';

export type CanonicalAuditSignatureAlgorithm = 'Ed25519';

export interface CanonicalAuditPacketInput {
  version: '1.0';
  packetId: string;
  orgId: string;
  customerId?: string;
  requestId: string;
  createdAt: string;
  domain: CanonicalAuditDomain;
  input: {
    prompt?: string;
    context?: unknown;
    trust?: unknown;
  };
  policy: {
    id: string;
    name: string;
    dsl: string;
    compiledConstraints: unknown;
  };
  decision: {
    modelId: string;
    outcome: unknown;
    scores?: unknown;
  };
  governance: {
    level: string;
    conformanceStatus?: string;
    driftRisk?: string;
    lineageDepth?: number;
    trustPolicy?: unknown;
  };
  treasury?: {
    price?: number;
    currency?: string;
    reserves?: unknown;
  };
}

export interface CanonicalAuditPacket extends CanonicalAuditPacketInput {
  signature: {
    algorithm: CanonicalAuditSignatureAlgorithm;
    value: string;
  };
}
