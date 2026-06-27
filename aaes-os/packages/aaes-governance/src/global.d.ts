import type { FaultJournal } from './faultJournal.js';
import type { PatternLedger } from './patternLedger.js';

declare global {
  // eslint-disable-next-line no-var
  var faultJournal: FaultJournal | undefined;
  // eslint-disable-next-line no-var
  var patternLedger: PatternLedger | undefined;
}

export {};
