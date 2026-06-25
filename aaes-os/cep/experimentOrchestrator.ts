import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

import { runMinimalCDP1 } from '../benchmarks/cdp1/runMinimalCDP1.js';

export interface ExperimentResult {
  id: string;
  driftScore: number;
  baseline: unknown;
  perturbed: unknown;
  timestamp: string;
}

/** CEP — minimal experiment orchestrator for CDP-1 slice. */
export class CEPOrchestrator {
  async runMinimalExperiment(): Promise<ExperimentResult> {
    const id = 'CDP1-MIN-001';
    const timestamp = new Date().toISOString();

    const result = await runMinimalCDP1();

    const experimentResult: ExperimentResult = {
      id,
      driftScore: result.driftScore,
      baseline: result.baseline,
      perturbed: result.perturbed,
      timestamp,
    };

    const dir = join('artifacts', 'cdp1');
    mkdirSync(dir, { recursive: true });
    const outPath = join(dir, `${id}-${timestamp.replace(/[:.]/g, '_')}.json`);
    writeFileSync(outPath, JSON.stringify(experimentResult, null, 2));

    return experimentResult;
  }
}
