import { createHash } from 'node:crypto';
import type {
  SovereignBlock,
  SovereignLedgerEntry,
  SovereignPayloadBlock,
  SovereignLineageBlock,
  SovereignAuthorityBlock,
  SovereignReplayBlock,
  SovereignTemporalBlock,
  SovereignFederationBlock,
  SovereignVerificationResult,
} from './types.js';

export class EvidenceSovereignLedger {
  private readonly entries: SovereignLedgerEntry[] = [];

  appendSovereignPayload(payload: unknown): SovereignLedgerEntry {
    const payloadHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(payload), 'utf8').digest('hex')}`;
    const block: SovereignPayloadBlock = { kind: 'SovereignPayload', payload, payloadHash };
    return this.appendBlock(block);
  }

  appendSovereignLineage(
    lineageNodes: { nodeId: string; parentNodeId: string | null; stage: string }[],
  ): SovereignLedgerEntry {
    const lineageHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(lineageNodes), 'utf8').digest('hex')}`;
    const block: SovereignLineageBlock = { kind: 'SovereignLineage', lineageNodes, lineageHash };
    return this.appendBlock(block);
  }

  appendSovereignAuthority(authorityRefs: string[]): SovereignLedgerEntry {
    const authorityHash = `sha3-256:${createHash('sha3-256').update(authorityRefs.join(','), 'utf8').digest('hex')}`;
    const block: SovereignAuthorityBlock = { kind: 'SovereignAuthority', authorityRefs, authorityHash };
    return this.appendBlock(block);
  }

  appendSovereignReplay(replayArtifacts: unknown[]): SovereignLedgerEntry {
    const replayHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(replayArtifacts), 'utf8').digest('hex')}`;
    const block: SovereignReplayBlock = { kind: 'SovereignReplay', replayArtifacts, replayHash };
    return this.appendBlock(block);
  }

  appendSovereignTemporal(timestamp: number, horizon: string): SovereignLedgerEntry {
    const temporalMetadata = { timestamp, horizon };
    const temporalHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(temporalMetadata), 'utf8').digest('hex')}`;
    const block: SovereignTemporalBlock = { kind: 'SovereignTemporal', temporalMetadata, temporalHash };
    return this.appendBlock(block);
  }

  appendSovereignFederation(worldId: string): SovereignLedgerEntry {
    const federationHash = `sha3-256:${createHash('sha3-256').update(worldId, 'utf8').digest('hex')}`;
    const block: SovereignFederationBlock = { kind: 'SovereignFederation', worldId, federationHash };
    return this.appendBlock(block);
  }

  verify(): SovereignVerificationResult {
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

  getEntries(): SovereignLedgerEntry[] {
    return [...this.entries];
  }

  private appendBlock(block: SovereignBlock): SovereignLedgerEntry {
    const previousEntryHash = this.entries.length > 0
      ? this.entries[this.entries.length - 1].entryHash
      : null;
    const entryHash = this.computeEntryHash(block, previousEntryHash);
    const entry: SovereignLedgerEntry = {
      sequence: this.entries.length + 1,
      block,
      previousEntryHash,
      entryHash,
      appendedAt: Date.now(),
    };
    this.entries.push(entry);
    return entry;
  }

  private computeEntryHash(block: SovereignBlock, previousEntryHash: string | null): string {
    const raw = `${JSON.stringify(block)}|${previousEntryHash ?? 'null'}`;
    return `sha3-256:${createHash('sha3-256').update(raw, 'utf8').digest('hex')}`;
  }
}
