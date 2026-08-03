import { createHash } from 'node:crypto';

export type StewardshipStage = 'intent' | 'authority' | 'evidence' | 'planning' | 'execution' | 'validation' | 'stewardship';

export type StewardshipRegisterId = 'CSIR' | 'CSAR' | 'CSER' | 'CSPR' | 'CSXR' | 'CSVR' | 'CSSR';

export type StewardshipGateKind =
  | 'StewardshipContinuityGate'
  | 'StewardshipReplayGate'
  | 'StewardshipLineageGate'
  | 'StewardshipAuthorityGate'
  | 'StewardshipEvidenceGate'
  | 'StewardshipFederationGate';

export interface StewardshipRegister {
  id: StewardshipRegisterId;
  stage: StewardshipStage;
  artifact: unknown;
  artifactHash: string;
  preservedAt: number;
}

export interface StewardshipGate {
  kind: StewardshipGateKind;
  passes: boolean;
  evaluatedAt: number;
  reason?: string;
}

export interface StewardshipAnchor {
  coordinate: string;
  stage: StewardshipStage;
  anchoredAt: number;
  stewardshipHash: string;
}

export interface StewardshipReplayNode {
  nodeId: string;
  stage: StewardshipStage;
  registerSnapshot: Record<StewardshipRegisterId, string>;
  gatesPassed: string[];
  parentNodeId: string | null;
  replayedAt: number;
}

export interface StewardshipFederationPort {
  worldId: string;
  lastSyncTimestamp: number;
  remoteStewardshipHash: string;
}

export interface CSMC {
  register: StewardshipRegister;
  gate: StewardshipGate;
  anchor: StewardshipAnchor;
  replayNode: StewardshipReplayNode;
  federationPort: StewardshipFederationPort | null;
}

export interface StewardshipReconstruction {
  nodeId: string;
  reconstructedLineage: StewardshipReplayNode[];
  isDeterministic: boolean;
  completedAt: number;
}

export interface StewardshipContinuityResult {
  isContinuous: boolean;
  breakAtIndex: number | null;
  checkedNodes: number;
}

export function hashStewardship(value: unknown): string {
  const raw = typeof value === 'string' ? value : JSON.stringify(value);
  return `sha3-256:${createHash('sha3-256').update(raw, 'utf8').digest('hex')}`;
}

export function createStewardshipRegister(stage: StewardshipStage, artifact: unknown): StewardshipRegister {
  const idMap: Record<StewardshipStage, StewardshipRegisterId> = {
    intent: 'CSIR',
    authority: 'CSAR',
    evidence: 'CSER',
    planning: 'CSPR',
    execution: 'CSXR',
    validation: 'CSVR',
    stewardship: 'CSSR',
  };
  return {
    id: idMap[stage],
    stage,
    artifact,
    artifactHash: hashStewardship(artifact),
    preservedAt: Date.now(),
  };
}
