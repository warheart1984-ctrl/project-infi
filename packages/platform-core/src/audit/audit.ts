export interface PricingAuditPacket {
  id: string;
  orgId: string;
  requestId: string;
  modelId: string;
  price: number;
  currency: string;
  breakdown: unknown;
  createdAt: string;
}

export interface RoutingAuditPacket {
  id: string;
  orgId: string;
  requestId: string;
  modelId: string;
  justification: unknown;
  createdAt: string;
}

export interface EntitlementsAuditPacket {
  id: string;
  orgId: string;
  customerId: string;
  entitlements: unknown;
  createdAt: string;
}

export interface AuditStore {
  getPricingAudit(orgId: string): Promise<PricingAuditPacket[]>;
  getRoutingAudit(orgId: string): Promise<RoutingAuditPacket[]>;
  getEntitlementsAudit(orgId: string): Promise<EntitlementsAuditPacket[]>;
}
