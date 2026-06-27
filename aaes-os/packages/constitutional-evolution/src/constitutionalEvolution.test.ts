import { describe, expect, it } from 'vitest';

import { buildMRIOutputV2, PILOT_AFTER, PILOT_BEFORE, PILOT_BENCHMARKS, runMRIComparison } from '@aaes-os/mri-instrument';
import {
  evaluateInvariantFitness,
  promoteInvariant,
  proposeInvariant,
  retainInvariant,
  revertInvariant,
} from './index.js';

describe('constitutional evolution loop', () => {
  it('proposes via Genesis and promotes positive high-confidence invariants', () => {
    const proposal = proposeInvariant({
      invariantId: 'INV-GENESIS-1',
      expression: 'require governance >= 70',
      mode: 'Genesis',
    });
    const mri = buildMRIOutputV2(runMRIComparison(PILOT_BEFORE, PILOT_AFTER), PILOT_BENCHMARKS);
    const decision = evaluateInvariantFitness({ proposal, mri });

    expect(proposal.status).toBe('proposed');
    expect(decision.decision).toBe('promote');
    expect(promoteInvariant(proposal.invariantId).stage).toBe('constitutional');
    expect(decision.lawOfLawsEntry.entryType).toBe('evolution_decision');
  });

  it('retains neutral and reverts harmful invariants with receipts', () => {
    const retained = retainInvariant('INV-NEUTRAL');
    const reverted = revertInvariant('INV-HARMFUL');

    expect(retained.decision).toBe('retain');
    expect(reverted.decision).toBe('revert');
    expect(reverted.receipt.receiptId).toMatch(/^evidence:/);
  });
});
