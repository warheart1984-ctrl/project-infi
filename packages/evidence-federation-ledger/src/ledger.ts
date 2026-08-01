import { createHash } from 'node:crypto';
import type {
  FederationBlock,
  FederationLedgerEntry,
  FederationPayloadBlock,
  FederationLineageBlock,
  FederationAuthorityBlock,
  FederationReplayBlock,
  FederationTemporalBlock,
  FederationStewardshipBlock,
  LedgerVerificationResult,
} from './types.js';

export class EvidenceFederationLedger {
  private readonly entries: FederationLedgerEntry[] = [];

  appendFederationPayload(metadata: unknown): FederationLedgerEntry {
    const metadataHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(metadata), 'utf8').digest('hex')}`;
    const block: FederationPayloadBlock = { kind: 'FederationPayload', metadata, metadataHash };
    return this.appendBlock(block);
  }

  appendFederationLineage(
    lineageNodes: { nodeId: string; parentNodeId: string | null; stage: string }[],
  ): FederationLedgerEntry {
    const lineageHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(lineageNodes), 'utf8').digest('hex')}`;
    const block: FederationLineageBlock = { kind: 'FederationLineage', lineageNodes, lineageHash };
    return this.appendBlock(block);
  }

  appendFederationAuthority(authorityRefs: string[]): FederationLedgerEntry {
    const authorityHash = `sha3-256:${createHash('sha3-256').update(authorityRefs.join(','), 'utf8').digest('hex')}`;
    const block: FederationAuthorityBlock = { kind: 'FederationAuthority', authorityRefs, authorityHash };
    return this.appendBlock(block);
  }

  appendFederationReplay(replayArtifacts: unknown[]): FederationLedgerEntry {
    const replayHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(replayArtifacts), 'utf8').digest('hex')}`;
    const block: FederationReplayBlock = { kind: 'FederationReplay', replayArtifacts, replayHash };
    return this.appendBlock(block);
  }

  appendFederationTemporal(timestamp: number, horizon: string): FederationLedgerEntry {
    const temporalMetadata = { timestamp, horizon };
    const temporalHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(temporalMetadata), 'utf8').digest('hex')}`;
    const block: FederationTemporalBlock = { kind: 'FederationTemporal', temporalMetadata, temporalHash };
    return this.appendBlock(block);
  }

  appendFederationStewardship(stewardId: string): FederationLedgerEntry {
    const stewardshipHash = `sha3-256:${createHash('sha3-256').update(stewardId, 'utf8').digest('hex')}`;
    const block: FederationStewardshipBlock = { kind: 'FederationStewardship', stewardId, stewardshipHash };
    return this.appendBlock(block);
  }

  verify(): LedgerVerificationResult {
    const violations: string[] = [];
    for (let i = 0; i < this.entries.length; i++) {
      const entry = this.entries[i];
      const expectedPreviousHash = i === 0 ? null : this.entries[i - 1].entryHash;
      if (entry.previousEntryHash !== expectedPreviousHash) {
        violations.push(`entry ${entry.sequence}: previousEntryHash mismatch`);
      }
      const expectedEntryHash = this.computeEntryHash(entry.block, entry.previousEntryHash);
      if (entry.entryHash !== expectedEntryHash) {
        violations.push(`entry ${entry.sequence}: entryHash mismatch`);
      }
    }
    return {
      isValid: violations.length === 0,
      entryCount: this.entries.length,
      violations,
    };
  }

  getEntries(): FederationLedgerEntry[] {
    return [...this.entries];
  }

  private appendBlock(block: FederationBlock): FederationLedgerEntry {
    const previousEntryHash = this.entries.length > 0
      ? this.entries[this.entries.length - 1].entryHash
      : null;
    const entryHash = this.computeEntryHash(block, previousEntryHash);
    const entry: FederationLedgerEntry = {
      sequence: this.entries.length + 1,
      block,
      previousEntryHash,
      entryHash,
      appendedAt: Date.now(),
    };
    this.entries.push(entry);
    return entry;
  }

  private computeEntryHash(block: FederationBlock, previousEntryHash: string | null): string {
    const raw = `${JSON.stringify(block)}|${previousEntryHash ?? 'null'}`;
    return `sha3-256:${createHash('sha3-256').update(raw, 'utf8').digest('hex')}`;
  }
}
