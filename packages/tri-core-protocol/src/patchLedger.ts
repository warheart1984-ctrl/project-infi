export type PatchStatus = 'PROPOSED' | 'APPROVED' | 'DEPLOYED' | 'REJECTED';

export interface PatchRecord {
  patchId: string;
  title: string;
  description: string;
  proposedBy: string;
  approvedBy: string[];
  status: PatchStatus;
  createdAt: string;
  updatedAt: string;
}

export class PatchLedger {
  private readonly patches = new Map<string, PatchRecord>();

  propose(patch: Omit<PatchRecord, 'status' | 'createdAt' | 'updatedAt' | 'approvedBy'>): PatchRecord {
    const now = new Date().toISOString();
    const record: PatchRecord = {
      ...patch,
      approvedBy: [],
      status: 'PROPOSED',
      createdAt: now,
      updatedAt: now,
    };
    this.patches.set(record.patchId, record);
    return record;
  }

  approve(patchId: string, approver: string): PatchRecord {
    const existing = this.patches.get(patchId);
    if (!existing) {
      throw new Error(`Unknown patch: ${patchId}`);
    }
    if (!existing.approvedBy.includes(approver)) {
      existing.approvedBy.push(approver);
    }
    existing.status = 'APPROVED';
    existing.updatedAt = new Date().toISOString();
    return existing;
  }

  reject(patchId: string): PatchRecord {
    const existing = this.patches.get(patchId);
    if (!existing) {
      throw new Error(`Unknown patch: ${patchId}`);
    }
    existing.status = 'REJECTED';
    existing.updatedAt = new Date().toISOString();
    return existing;
  }

  markDeployed(patchId: string): PatchRecord {
    const existing = this.patches.get(patchId);
    if (!existing) {
      throw new Error(`Unknown patch: ${patchId}`);
    }
    if (existing.status !== 'APPROVED') {
      throw new Error(`Patch ${patchId} must be APPROVED before deploy`);
    }
    existing.status = 'DEPLOYED';
    existing.updatedAt = new Date().toISOString();
    return existing;
  }

  list(): PatchRecord[] {
    return [...this.patches.values()].sort((a, b) => a.patchId.localeCompare(b.patchId));
  }

  get(patchId: string): PatchRecord | undefined {
    return this.patches.get(patchId);
  }

  clear(): void {
    this.patches.clear();
  }
}
