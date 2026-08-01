import { createHash } from 'node:crypto';
import type {
  LineageBlock,
  LineageLedgerEntry,
  LineagePayloadBlock,
  LineageChainBlock,
  LineageNode,
  LineageAuthorityBlock,
  LineageReplayBlock,
  LineageTemporalBlock,
  LineageFederationBlock,
  LineageVerificationResult,
} from './types.js';

export class EvidenceLineageLedger {
  private readonly entries: LineageLedgerEntry[] = [];

  appendLineagePayload(payload: unknown): LineageLedgerEntry {
    const payloadHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(payload), 'utf8').digest('hex')}`;
    const block: LineagePayloadBlock = { kind: 'LineagePayload', payload, payloadHash };
    return this.appendBlock(block);
  }

  appendLineageChain(nodes: LineageNode[]): LineageLedgerEntry {
    const chainHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(nodes), 'utf8').digest('hex')}`;
    const block: LineageChainBlock = { kind: 'LineageChain', nodes, chainHash };
    return this.appendBlock(block);
  }

  appendLineageAuthority(authorityRefs: string[]): LineageLedgerEntry {
    const authorityHash = `sha3-256:${createHash('sha3-256').update(authorityRefs.join(','), 'utf8').digest('hex')}`;
    const block: LineageAuthorityBlock = { kind: 'LineageAuthority', authorityRefs, authorityHash };
    return this.appendBlock(block);
  }

  appendLineageReplay(replayArtifacts: unknown[]): LineageLedgerEntry {
    const replayHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(replayArtifacts), 'utf8').digest('hex')}`;
    const block: LineageReplayBlock = { kind: 'LineageReplay', replayArtifacts, replayHash };
    return this.appendBlock(block);
  }

  appendLineageTemporal(timestamp: number, horizon: string): LineageLedgerEntry {
    const temporalMetadata = { timestamp, horizon };
    const temporalHash = `sha3-256:${createHash('sha3-256').update(JSON.stringify(temporalMetadata), 'utf8').digest('hex')}`;
    const block: LineageTemporalBlock = { kind: 'LineageTemporal', temporalMetadata, temporalHash };
    return this.appendBlock(block);
  }

  appendLineageFederation(worldId: string): LineageLedgerEntry {
    const federationHash = `sha3-256:${createHash('sha3-256').update(worldId, 'utf8').digest('hex')}`;
    const block: LineageFederationBlock = { kind: 'LineageFederation', worldId, federationHash };
    return this.appendBlock(block);
  }

  verify(): LineageVerificationResult {
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

  getEntries(): LineageLedgerEntry[] {
    return [...this.entries];
  }

  private appendBlock(block: LineageBlock): LineageLedgerEntry {
    const previousEntryHash = this.entries.length > 0
      ? this.entries[this.entries.length - 1].entryHash
      : null;
    const entryHash = this.computeEntryHash(block, previousEntryHash);
    const entry: LineageLedgerEntry = {
      sequence: this.entries.length + 1,
      block,
      previousEntryHash,
      entryHash,
      appendedAt: Date.now(),
    };
    this.entries.push(entry);
    return entry;
  }

  private computeEntryHash(block: LineageBlock, previousEntryHash: string | null): string {
    const raw = `${JSON.stringify(block)}|${previousEntryHash ?? 'null'}`;
    return `sha3-256:${createHash('sha3-256').update(raw, 'utf8').digest('hex')}`;
  }
}
