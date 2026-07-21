import type { CognitiveRisk } from '@aaes-os/governed-runtime';

export type GovernanceMode = 'strict' | 'balanced' | 'experimental';
export type CustomerPlanId = 'free' | 'pro' | 'enterprise';
export type CustomerAuthProvider = 'email' | 'google' | 'microsoft' | 'github' | 'apple';
export type OrganizationRole = 'owner' | 'admin' | 'analyst' | 'developer' | 'auditor';
export type OrgRole = OrganizationRole;

export interface Org {
  id: string;
  name: string;
  ownerId: string;
  planId: string;
  createdAt: string;
  updatedAt: string;
}

export interface OrgMember {
  orgId: string;
  customerId: string;
  role: OrgRole;
  createdAt: string;
}

export interface CustomerEntitlements {
  maxRequestsPerMonth: number;
  maxTokensPerMonth: number;
  allowedModels: string[];
  routingTier: 'basic' | 'pro' | 'enterprise';
  codexPacketHandoff: boolean;
  usageLedger: boolean;
  marginDashboard: boolean;
  treasuryAccess: boolean;
  governanceLevel: 'basic' | 'enhanced' | 'full';
  auditScope: 'personal' | 'team' | 'org';
  overageBillingEnabled: boolean;
  customerAuditSurfaces: boolean;
}

export interface OrganizationMemberRecord {
  customerId: string;
  role: OrganizationRole;
  joinedAt: string;
}

export interface OrganizationRecord {
  id: string;
  name: string;
  ownerCustomerId: string;
  planId: string;
  billingContactEmail: string;
  domain?: string;
  members: OrganizationMemberRecord[];
  createdAt: string;
  updatedAt: string;
}

export interface CustomerRecord {
  id: string;
  ownerId: string;
  email: string;
  displayName?: string;
  authProvider: CustomerAuthProvider;
  authSubject?: string;
  passwordHash?: string;
  planId: CustomerPlanId;
  planName: string;
  entitlements: CustomerEntitlements;
  organizationId?: string;
  organizationRole?: OrganizationRole;
  createdAt: string;
  updatedAt: string;
}

export interface CustomerSession {
  sessionId: string;
  customerId: string;
  ownerId: string;
  email: string;
  planId: CustomerPlanId;
  planName: string;
  entitlements: CustomerEntitlements;
  governanceProfile: GovernanceMode;
  organizationId?: string;
  organizationRole?: OrganizationRole;
  createdAt: string;
  expiresAt: string;
}

export interface GovernanceProfile {
  id: GovernanceMode;
  name: string;
  description: string;
  invariantSets: string[];
  riskThreshold: CognitiveRisk;
  allowedAgentBehaviors: string[];
  billingTier: 'enterprise' | 'standard' | 'sandbox';
  apiAccessLevel: 'full' | 'standard' | 'experimental';
  marketplaceAccess: boolean;
}

export interface SemVer {
  major: number;
  minor: number;
  patch: number;
  prerelease?: string;
}

export interface CapabilityVersion {
  version: string;
  semver: SemVer;
  moduleId: string;
  organId: string;
  publishedAt: string;
  changelog?: string;
  compatibility: {
    minPlatform: string;
    maxRisk: CognitiveRisk;
    requiredInvariants: string[];
  };
  deprecated?: boolean;
}

export interface CapabilityRecord {
  id: string;
  name: string;
  description: string;
  organId: string;
  ownerId: string;
  currentVersion: string;
  versions: CapabilityVersion[];
  governanceProfile: GovernanceMode;
  createdAt: string;
  updatedAt: string;
}

export interface ApiKeyRecord {
  id: string;
  label: string;
  keyPrefix: string;
  keyHash: string;
  ownerId: string;
  governanceProfile: GovernanceMode;
  scopes: string[];
  createdAt: string;
  lastUsedAt?: string;
  revoked: boolean;
}

export interface UsageRecord {
  id: string;
  ownerId: string;
  orgId?: string;
  customerId?: string;
  capabilityId?: string;
  operation: string;
  units: number;
  governanceProfile: GovernanceMode;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface UsageEvent {
  id: string;
  orgId: string;
  customerId?: string;
  kind: string;
  amount: number;
  metadata?: Record<string, unknown>;
  occurredAt: string;
}

export interface OverageEvent {
  id: string;
  orgId: string;
  kind: string;
  amount: number;
  metadata?: Record<string, unknown>;
  occurredAt: string;
}

export interface AuthSession {
  sessionId: string;
  ownerId: string;
  governanceProfile: GovernanceMode;
  createdAt: string;
  expiresAt: string;
}

export interface InvokeRequest {
  capabilityId: string;
  version?: string;
  input: Record<string, unknown>;
  traceId?: string;
}

export interface InvokeResult {
  capabilityId: string;
  version: string;
  output: Record<string, unknown>;
  governance: {
    profile: GovernanceMode;
    violations: string[];
    allowed: boolean;
  };
  billing: {
    units: number;
    operation: string;
  };
}

export interface CompatibilityResult {
  compatible: boolean;
  reasons: string[];
  sourceVersion: string;
  targetVersion: string;
}
