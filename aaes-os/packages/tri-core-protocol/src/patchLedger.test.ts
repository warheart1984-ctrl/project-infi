import { describe, expect, it } from 'vitest';
import { PatchLedger } from './patchLedger.js';

describe('PatchLedger', () => {
  it('approves and deploys patches', () => {
    const ledger = new PatchLedger();
    const p = ledger.propose({
      patchId: 'PATCH_TEST_001',
      title: 'Test',
      description: 'd',
      proposedBy: 'EXECUTION_CORE',
    });
    expect(p.status).toBe('PROPOSED');
    ledger.approve(p.patchId, 'GOVERNANCE');
    ledger.approve(p.patchId, 'ARCHITECTURE');
    const deployed = ledger.markDeployed(p.patchId);
    expect(deployed?.status).toBe('DEPLOYED');
    expect(ledger.list().filter((patch) => patch.status === 'DEPLOYED')).toHaveLength(1);
  });

  it('rejects patches', () => {
    const ledger = new PatchLedger();
    const p = ledger.propose({
      patchId: 'PATCH_REJECT',
      title: 'R',
      description: 'd',
      proposedBy: 'EXECUTION_CORE',
    });
    ledger.reject(p.patchId);
    expect(ledger.get(p.patchId)?.status).toBe('REJECTED');
  });
});
