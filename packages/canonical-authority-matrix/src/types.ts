import { createHash, randomUUID } from 'node:crypto';

export type AuthorityStage = 'intent' | 'authority' | 'evidence' | 'planning' | 'execution' | 'validation' | 'stewardship';

export type AuthorityRegisterId = 'AIR' | 'AAR' | 'AER' | 'APR' | 'AXR' | 'AVR' | 'ASR';

export type AuthorityGateKind =
  | 'AuthorityLegitimacyGate'
  | 'AuthorityContinuityGate'
  | 'AuthorityReplayGate'
  | 'AuthorityLineageGate'
  | 'AuthorityEvidenceGate'
  | 'AuthorityFederationGate';

export interface AuthorityRegister {
  id: AuthorityRegisterId;
  stage: AuthorityStage;
  artifact: unknown;
  artifactHash: string;
  authorityNonce: string;
  registeredAt: number;
}

export interface AuthorityGate {
  kind: AuthorityGateKind;
  passes: boolean;
  evaluatedAt: number;
  reason?: string;
}

export interface AuthorityAnchor {
  coordinate: string;
  stage: AuthorityStage;
  anchoredAt: number;
  authorityHash: string;
}

export interface AuthorityReplayNode {
  nodeId: string;
  stage: AuthorityStage;
  registerSnapshot: Record<AuthorityRegisterId, string>;
  gatesPassed: string[];
  parentNodeId: string | null;
  replayedAt: number;
}

export interface AuthorityFederationPort {
  worldId: string;
  lastSyncTimestamp: number;
  remoteAuthorityHash: string;
}

export interface CAMC {
  register: AuthorityRegister;
  gate: AuthorityGate;
  anchor: AuthorityAnchor;
  replayNode: AuthorityReplayNode;
  federationPort: AuthorityFederationPort | null;
}

export interface AuthorityReconstruction {
  nodeId: string;
  reconstructedLineage: AuthorityReplayNode[];
  isDeterministic: boolean;
  completedAt: number;
}

export interface AuthorityContinuityResult {
  isContinuous: boolean;
  breakAtIndex: number | null;
  checkedNodes: number;
}

export function hashAuthority(value: unknown): string {
  const raw = typeof value === 'string' ? value : JSON.stringify(value);
  return `sha3-256:${createHash('sha3-256').update(raw, 'utf8').digest('hex')}`;
}

export function createAuthorityRegister(stage: AuthorityStage, artifact: unknown): AuthorityRegister {
  const idMap: Record<AuthorityStage, AuthorityRegisterId> = {
    intent: 'AIR',
    authority: 'AAR',
    evidence: 'AER',
    planning: 'APR',
    execution: 'AXR',
    validation: 'AVR',
    stewardship: 'ASR',
  };
  return {
    id: idMap[stage],
    stage,
    artifact,
    artifactHash: hashAuthority(artifact),
    authorityNonce: randomUUID(),
    registeredAt: Date.now(),
  };
}
