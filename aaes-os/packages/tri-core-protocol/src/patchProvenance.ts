import { createHash } from 'node:crypto';

export interface ProvenanceEntry {
  patchId: string;
  action: 'PROPOSED' | 'APPROVED' | 'DEPLOYED' | 'REJECTED';
  actor: string;
  timestamp: string;
  prevHash: string;
  hash: string;
}

export class PatchProvenanceChain {
  private chain: ProvenanceEntry[] = [];

  append(entry: Omit<ProvenanceEntry, 'prevHash' | 'hash'>): ProvenanceEntry {
    const prevHash = this.chain.length > 0 ? this.chain[this.chain.length - 1]!.hash : 'GENESIS';
    const payload = JSON.stringify({ ...entry, prevHash });
    const hash = createHash('sha256').update(payload).digest('hex');
    const full: ProvenanceEntry = { ...entry, prevHash, hash };
    this.chain.push(full);
    return full;
  }

  list(): ProvenanceEntry[] {
    return [...this.chain];
  }

  verify(): boolean {
    let prev = 'GENESIS';
    for (const entry of this.chain) {
      if (entry.prevHash !== prev) {
        return false;
      }
      const payload = JSON.stringify({
        patchId: entry.patchId,
        action: entry.action,
        actor: entry.actor,
        timestamp: entry.timestamp,
        prevHash: entry.prevHash,
      });
      const expected = createHash('sha256').update(payload).digest('hex');
      if (expected !== entry.hash) {
        return false;
      }
      prev = entry.hash;
    }
    return true;
  }

  clear(): void {
    this.chain = [];
  }
}
