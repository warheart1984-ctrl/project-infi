import { PatternLedger } from '@aaes-os/aaes-governance';
import {
  PlatformService,
  type GovernanceMode,
  type PlatformContext,
} from '@aaes-os/platform-core';
import { MeshNetwork } from '@aaes-os/platform-mesh';
import { PsomMesh } from '@aaes-os/psom-mesh';
import { SgceEconomy } from '@aaes-os/sgce';
import { AuthorityLevel, SovrenAuthority } from '@aaes-os/sovren';

const LAW_KEY = process.env.SOVREN_LAW_KEY ?? 'platform-api-dev-key';
const LAW_HASH = process.env.PLATFORM_LAW_HASH ?? 'platform-law-v1';
const ORGANISM_ID = process.env.ORGANISM_ID ?? 'organism-local';
const API_PORT = Number(process.env.PLATFORM_API_PORT ?? 4100);

export const platform = new PlatformService();
export const ledger = new PatternLedger();
export const sovren = new SovrenAuthority(LAW_KEY);
export const mesh = new MeshNetwork(ORGANISM_ID, LAW_HASH, sovren, ledger);
export const sgce = new SgceEconomy();
export const psom = new PsomMesh({
  nodeId: ORGANISM_ID,
  organismId: ORGANISM_ID,
  endpoint: `http://localhost:${API_PORT}`,
  governanceProfile: 'balanced',
  federation: undefined,
});

// Register local node in PSOM registry
psom.registry.register({
  nodeId: ORGANISM_ID,
  organismId: ORGANISM_ID,
  endpoint: `http://localhost:${API_PORT}`,
  governanceProfile: 'balanced',
});

export function resolveContext(req: {
  header(name: string): string | undefined;
}): PlatformContext {
  const auth = req.header('authorization');
  if (auth?.startsWith('Bearer org_')) {
    return platform.authenticateApiKey(auth.slice(7));
  }
  const sessionId = req.header('x-session-id');
  if (sessionId) {
    const customerSession = platform.getCustomerSession(sessionId);
    if (customerSession) {
      const organization = customerSession.organizationId ? platform.getOrganization(customerSession.organizationId) : undefined;
      return {
        ownerId: customerSession.ownerId,
        customerId: customerSession.customerId,
        planId: customerSession.planId,
        customer: platform.getCustomer(customerSession.customerId),
        entitlements: customerSession.entitlements,
        organizationId: customerSession.organizationId,
        organizationRole: customerSession.organizationRole,
        organization,
        governanceProfile: customerSession.governanceProfile,
        scopes: ['*'],
      };
    }
    const session = platform.apiKeys.getSession(sessionId);
    if (session) {
      return {
        ownerId: session.ownerId,
        governanceProfile: session.governanceProfile,
        scopes: ['*'],
      };
    }
  }
  throw new Error('AUTH: missing or invalid credentials');
}

export function sovereignToken(actorId: string) {
  return sovren.issue(actorId, AuthorityLevel.SOVEREIGN_ROOT);
}

export function parseGovernanceMode(value: unknown): GovernanceMode {
  if (value === 'strict' || value === 'balanced' || value === 'experimental') {
    return value;
  }
  return 'balanced';
}
