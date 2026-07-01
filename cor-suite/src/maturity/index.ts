import { COR_SUITE_PATHS } from "../paths.js";
import type { CorStateVector, MaturityLevel } from "../types/cor.js";
import type { MaturityVector } from "../types/maturity.js";
import { readJsonInput, writeJsonOutput } from "../lib/io.js";

export function computeMaturity(cor?: CorStateVector): MaturityVector {
  const corState = cor ?? readJsonInput<CorStateVector>(COR_SUITE_PATHS.outputs.corState);
  const requirements = corState.requirements.map((r) => ({
    requirementId: r.id,
    maturity: r.maturity,
  }));

  const summary: Record<MaturityLevel, number> = {
    normative: 0,
    implemented: 0,
    verified: 0,
    reproduced: 0,
  };
  for (const r of requirements) summary[r.maturity] += 1;

  return {
    generatedAt: new Date().toISOString(),
    commit: corState.commit,
    requirements,
    summary,
  };
}

export function emitMaturityVector(cor?: CorStateVector): string {
  return writeJsonOutput(COR_SUITE_PATHS.outputs.maturityVector, computeMaturity(cor));
}
