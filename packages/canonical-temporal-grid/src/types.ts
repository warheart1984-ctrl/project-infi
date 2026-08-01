import { createHash } from 'node:crypto';

export type TemporalStage = 'intent' | 'authority' | 'evidence' | 'planning' | 'execution' | 'validation' | 'stewardship';

export type TemporalRegisterId = 'CTIR' | 'CTAR' | 'CTER' | 'CTPR' | 'CTXR' | 'CTVR' | 'CTSR';

export type TemporalGateKind =
  | 'TemporalOrderGate'
  | 'TemporalContinuityGate'
  | 'TemporalReplayGate'
  | 'TemporalLineageGate'
  | 'TemporalAuthorityGate'
  | 'TemporalFederationGate';

export interface TemporalRegister {
  id: TemporalRegisterId;
  stage: TemporalStage;
  artifact: unknown;
  artifactHash: string;
  temporalOrder: number;
  registeredAt: number;
}

export interface TemporalGate {
  kind: TemporalGateKind;
  passes: boolean;
  evaluatedAt: number;
  reason?: string;
}

export interface TemporalAnchor {
  coordinate: string;
  stage: TemporalStage;
  anchoredAt: number;
  temporalHash: string;
}

export interface TemporalReplayNode {
  nodeId: string;
  stage: TemporalStage;
  registerSnapshot: Record<TemporalRegisterId, string>;
  gatesPassed: string[];
  parentNodeId: string | null;
  replayedAt: number;
}

export interface TemporalFederationPort {
  worldId: string;
  lastSyncTimestamp: number;
  remoteTemporalHash: string;
}

export interface CTGC {
  register: TemporalRegister;
  gate: TemporalGate;
  anchor: TemporalAnchor;
  replayNode: TemporalReplayNode;
  federationPort: TemporalFederationPort | null;
}

export interface TemporalReconstruction {
  nodeId: string;
  reconstructedLineage: TemporalReplayNode[];
  isDeterministic: boolean;
  completedAt: number;
}

export interface TemporalContinuityResult {
  isContinuous: boolean;
  breakAtIndex: number | null;
  checkedNodes: number;
}

export function hashTemporal(value: unknown): string {
  const raw = typeof value === 'string' ? value : JSON.stringify(value);
  return `sha3-256:${createHash('sha3-256').update(raw, 'utf8').digest('hex')}`;
}

let temporalCounter = 0;

export function createTemporalRegister(stage: TemporalStage, artifact: unknown): TemporalRegister {
  const idMap: Record<TemporalStage, TemporalRegisterId> = {
    intent: 'CTIR',
    authority: 'CTAR',
    evidence: 'CTER',
    planning: 'CTPR',
    execution: 'CTXR',
    validation: 'CTVR',
    stewardship: 'CTSR',
  };
  temporalCounter++;
  return {
    id: idMap[stage],
    stage,
    artifact,
    artifactHash: hashTemporal(artifact),
    temporalOrder: temporalCounter,
    registeredAt: Date.now(),
  };
}
