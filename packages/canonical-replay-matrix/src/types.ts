import { createHash } from 'node:crypto';

export type ReplayStage = 'intent' | 'authority' | 'evidence' | 'planning' | 'execution' | 'validation' | 'stewardship';

export type ReplayRegisterId = 'CRIR' | 'CRAR' | 'CRER' | 'CRPR' | 'CRXR' | 'CRVR' | 'CRSR';

export type ReplayGateKind =
  | 'CanonicalReplayDeterminismGate'
  | 'CanonicalReplayContinuityGate'
  | 'CanonicalReplayLineageGate'
  | 'CanonicalReplayAuthorityGate'
  | 'CanonicalReplayEvidenceGate'
  | 'CanonicalReplayFederationGate';

export interface ReplayRegister {
  id: ReplayRegisterId;
  stage: ReplayStage;
  artifact: unknown;
  artifactHash: string;
  replayedAt: number;
}

export interface ReplayGate {
  kind: ReplayGateKind;
  passes: boolean;
  evaluatedAt: number;
  reason?: string;
}

export interface ReplayAnchor {
  coordinate: string;
  stage: ReplayStage;
  anchoredAt: number;
  artifactHash: string;
}

export interface ReplayNode {
  nodeId: string;
  stage: ReplayStage;
  registerSnapshot: Record<ReplayRegisterId, string>;
  gatesPassed: string[];
  parentNodeId: string | null;
  replayedAt: number;
}

export interface ReplayFederationPort {
  worldId: string;
  lastSyncTimestamp: number;
  remoteNodeId: string;
  remoteArtifactHash: string;
}

export interface CRMC {
  register: ReplayRegister;
  gate: ReplayGate;
  anchor: ReplayAnchor;
  node: ReplayNode;
  federationPort: ReplayFederationPort | null;
}

export interface ReplayReconstruction {
  nodeId: string;
  reconstructedLineage: ReplayNode[];
  isDeterministic: boolean;
  completedAt: number;
}

export interface ReplayContinuityResult {
  isContinuous: boolean;
  breakAtIndex: number | null;
  checkedNodes: number;
}

export interface ReplayFederationSync {
  worldId: string;
  synchronizedNodes: string[];
  conflicts: string[];
  syncedAt: number;
}

export function hashArtifact(value: unknown): string {
  const raw = typeof value === 'string' ? value : JSON.stringify(value);
  return `sha3-256:${createHash('sha3-256').update(raw, 'utf8').digest('hex')}`;
}

export function createReplayRegister(stage: ReplayStage, artifact: unknown): ReplayRegister {
  const idMap: Record<ReplayStage, ReplayRegisterId> = {
    intent: 'CRIR',
    authority: 'CRAR',
    evidence: 'CRER',
    planning: 'CRPR',
    execution: 'CRXR',
    validation: 'CRVR',
    stewardship: 'CRSR',
  };
  return {
    id: idMap[stage],
    stage,
    artifact,
    artifactHash: hashArtifact(artifact),
    replayedAt: Date.now(),
  };
}
