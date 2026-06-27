import { useMemo } from 'react';

import { createSubstrateSnapshot } from '../state/substrateStreams.js';
import type { SkillzMcgeeLedgerSummary } from '../state/studioState.js';

export function useSubstrateEvents(skillzmcgee: SkillzMcgeeLedgerSummary) {
  return useMemo(() => createSubstrateSnapshot(skillzmcgee), [skillzmcgee]);
}
