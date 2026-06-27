import type { FaultEvent } from './faultTypes.js';
import type { PatternRecord } from './patternLedger.js';

export interface DriftScore {
  score: number;
  totalFaults: number;
  uniquePatterns: number;
  topPatterns: PatternRecord[];
}

/**
 * v0.1 drift heuristic:
 * - More faults → higher drift
 * - More unique patterns → higher drift
 * - Normalized to 0–1 for now
 */
export class DriftMetrics {
  computeDrift(faults: FaultEvent[], patterns: PatternRecord[]): DriftScore {
    const totalFaults = faults.length;
    const uniquePatterns = patterns.length;

    if (totalFaults === 0) {
      return {
        score: 0,
        totalFaults: 0,
        uniquePatterns: 0,
        topPatterns: [],
      };
    }

    const faultComponent = Math.min(1, totalFaults / 20);
    const patternComponent = Math.min(1, uniquePatterns / 10);
    const score = Number((faultComponent * 0.7 + patternComponent * 0.3).toFixed(2));

    return {
      score,
      totalFaults,
      uniquePatterns,
      topPatterns: patterns
        .sort((a, b) => b.recurrence - a.recurrence)
        .slice(0, 5),
    };
  }
}
