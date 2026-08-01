import { createHash } from 'node:crypto';

export type LineageBlockKind =
  | 'LineagePayload'
  | 'LineageChain'
  | 'LineageAuthority'
  | 'LineageReplay'
  | 'LineageTemporal'
  | 'LineageFederation';

export interface LineagePayloadBlock {
  kind: 'LineagePayload';
  payload: unknown;
  payloadHash: string;
}

export interface LineageNode {
  nodeId: string;
  parentNodeId: string | null;
  stage: string;
  lineageHash: string;
}

export interface LineageChainBlock {
  kind: 'LineageChain';
  nodes: LineageNode[];
  chainHash: string;
}

export interface LineageAuthorityBlock {
  kind: 'LineageAuthority';
  authorityRefs: string[];
  authorityHash: string;
}

export interface LineageReplayBlock {
  kind: 'LineageReplay';
  replayArtifacts: unknown[];
  replayHash: string;
}

export interface LineageTemporalBlock {
  kind: 'LineageTemporal';
  temporalMetadata: { timestamp: number; horizon: string };
  temporalHash: string;
}

export interface LineageFederationBlock {
  kind: 'LineageFederation';
  worldId: string;
  federationHash: string;
}

export type LineageBlock =
  | LineagePayloadBlock
  | LineageChainBlock
  | LineageAuthorityBlock
  | LineageReplayBlock
  | LineageTemporalBlock
  | LineageFederationBlock;

export interface LineageLedgerEntry {
  sequence: number;
  block: LineageBlock;
  previousEntryHash: string | null;
  entryHash: string;
  appendedAt: number;
}

export type LineageLedgerOperation =
  | 'AppendLineagePayload'
  | 'AppendLineageChain'
  | 'AppendLineageAuthority'
  | 'AppendLineageReplay'
  | 'AppendLineageTemporal'
  | 'AppendLineageFederation'
  | 'VerifyLineageLedger';

export interface LineageVerificationResult {
  isValid: boolean;
  entryCount: number;
  violations: string[];
}

export function hashLineageBlock(block: LineageBlock): string {
  return `sha3-256:${createHash('sha3-256').update(JSON.stringify(block), 'utf8').digest('hex')}`;
}
