import { useMemo } from 'react';

import type { EnforcementSummary, SkillzMcgeeLedgerSummary } from '../state/studioState.js';

export function useGovernanceReceipts(skillzmcgee: SkillzMcgeeLedgerSummary, enforcement: EnforcementSummary) {
  return useMemo(() => [
    ...skillzmcgee.recentReceipts.map((receipt) => ({
      id: receipt.id,
      source: 'SkillzMcGee',
      status: receipt.status,
      detail: receipt.slice,
    })),
    ...enforcement.events.map((event) => ({
      id: event.receiptId,
      source: 'CEN',
      status: event.verdict,
      detail: event.reasonCode,
    })),
  ], [enforcement.events, skillzmcgee.recentReceipts]);
}
