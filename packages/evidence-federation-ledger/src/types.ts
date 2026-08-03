import { createHash } from 'node:crypto';

export type FederationBlockKind =
  | 'FederationPayload'
  | 'FederationLineage'
  | 'FederationAuthority'
  | 'FederationReplay'
  | 'FederationTemporal'
  | 'FederationStewardship';

export interface FederationPayloadBlock {
  kind: 'FederationPayload';
  metadata: unknown;
  metadataHash: string;
}

export interface FederationLineageBlock {
  kind: 'FederationLineage';
  lineageNodes: { nodeId: string; parentNodeId: string | null; stage: string }[];
  lineageHash: string;
}

export interface FederationAuthorityBlock {
  kind: 'FederationAuthority';
  authorityRefs: string[];
  authorityHash: string;
}

export interface FederationReplayBlock {
  kind: 'FederationReplay';
  replayArtifacts: unknown[];
  replayHash: string;
}

export interface FederationTemporalBlock {
  kind: 'FederationTemporal';
  temporalMetadata: { timestamp: number; horizon: string };
  temporalHash: string;
}

export interface FederationStewardshipBlock {
  kind: 'FederationStewardship';
  stewardId: string;
  stewardshipHash: string;
}

export type FederationBlock =
  | FederationPayloadBlock
  | FederationLineageBlock
  | FederationAuthorityBlock
  | FederationReplayBlock
  | FederationTemporalBlock
  | FederationStewardshipBlock;

export interface FederationLedgerEntry {
  sequence: number;
  block: FederationBlock;
  previousEntryHash: string | null;
  entryHash: string;
  appendedAt: number;
}

export type LedgerOperation =
  | 'AppendFederationPayload'
  | 'AppendFederationLineage'
  | 'AppendFederationAuthority'
  | 'AppendFederationReplay'
  | 'AppendFederationTemporal'
  | 'AppendFederationStewardship'
  | 'VerifyFederationLedger';

export interface LedgerVerificationResult {
  isValid: boolean;
  entryCount: number;
  violations: string[];
}

export function hashBlock(block: FederationBlock): string {
  return `sha3-256:${createHash('sha3-256').update(JSON.stringify(block), 'utf8').digest('hex')}`;
}
