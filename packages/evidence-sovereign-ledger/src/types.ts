import { createHash } from 'node:crypto';

export type SovereignBlockKind =
  | 'SovereignPayload'
  | 'SovereignLineage'
  | 'SovereignAuthority'
  | 'SovereignReplay'
  | 'SovereignTemporal'
  | 'SovereignFederation';

export interface SovereignPayloadBlock {
  kind: 'SovereignPayload';
  payload: unknown;
  payloadHash: string;
}

export interface SovereignLineageBlock {
  kind: 'SovereignLineage';
  lineageNodes: { nodeId: string; parentNodeId: string | null; stage: string }[];
  lineageHash: string;
}

export interface SovereignAuthorityBlock {
  kind: 'SovereignAuthority';
  authorityRefs: string[];
  authorityHash: string;
}

export interface SovereignReplayBlock {
  kind: 'SovereignReplay';
  replayArtifacts: unknown[];
  replayHash: string;
}

export interface SovereignTemporalBlock {
  kind: 'SovereignTemporal';
  temporalMetadata: { timestamp: number; horizon: string };
  temporalHash: string;
}

export interface SovereignFederationBlock {
  kind: 'SovereignFederation';
  worldId: string;
  federationHash: string;
}

export type SovereignBlock =
  | SovereignPayloadBlock
  | SovereignLineageBlock
  | SovereignAuthorityBlock
  | SovereignReplayBlock
  | SovereignTemporalBlock
  | SovereignFederationBlock;

export interface SovereignLedgerEntry {
  sequence: number;
  block: SovereignBlock;
  previousEntryHash: string | null;
  entryHash: string;
  appendedAt: number;
}

export type SovereignLedgerOperation =
  | 'AppendSovereignPayload'
  | 'AppendSovereignLineage'
  | 'AppendSovereignAuthority'
  | 'AppendSovereignReplay'
  | 'AppendSovereignTemporal'
  | 'AppendSovereignFederation'
  | 'VerifySovereignLedger';

export interface SovereignVerificationResult {
  isValid: boolean;
  entryCount: number;
  violations: string[];
}

export function hashSovereignBlock(block: SovereignBlock): string {
  return `sha3-256:${createHash('sha3-256').update(JSON.stringify(block), 'utf8').digest('hex')}`;
}
