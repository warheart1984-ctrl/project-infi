import type { CorStateVector } from "../types/cor.js";
import type { ProofAnalysisResult } from "../types/analysis.js";
import type { GovernanceReceipt } from "../types/governance.js";
import type { MaturityVector } from "../types/maturity.js";
import type { RepoHygieneStatus } from "../types/hygiene.js";
import { emitCorState, validateAndEmitCav } from "../cor/index.js";
import { emitCavReport } from "../cav/index.js";
import { emitProofAnalysis } from "../analysis/index.js";
import { emitMaturityVector } from "../maturity/index.js";
import { emitGovernanceReceipt } from "../governance/engine.js";
import { emitPgi } from "../pgi/index.js";
import { emitDra } from "../dra/index.js";
import { emitCsr } from "../csr/index.js";
import { emitRepoHygiene, hygienePasses, scanRepoHygiene } from "./scanner.js";
import { readJsonInput } from "../lib/io.js";
import { COR_SUITE_PATHS } from "../paths.js";
import { loadCarRegistry } from "../car/registry.js";

export interface PipelineResult {
  hygiene: RepoHygieneStatus;
  corPath: string;
  pgiPath: string;
  draPath: string;
  csrPath: string;
  analysisPath: string;
  maturityPath: string;
  governancePath: string;
  governance: GovernanceReceipt;
}

export async function runCorSuitePipeline(options?: {
  steward?: string;
  scope?: string[];
}): Promise<PipelineResult> {
  emitRepoHygiene();
  const hygiene = readJsonInput<RepoHygieneStatus>(COR_SUITE_PATHS.outputs.repoHygiene);

  const cav = validateAndEmitCav();
  if (!cav.valid) {
    throw new Error(`CAV-1.0 validation failed — see ${cav.path}`);
  }
  emitCavReport();

  const car = loadCarRegistry();
  const corPath = await emitCorState();
  const cor = readJsonInput<CorStateVector>(corPath);

  const pgiPath = emitPgi(car);
  const draPath = emitDra(car);

  const analysisPath = emitProofAnalysis(cor);
  const analysis = readJsonInput<ProofAnalysisResult>(analysisPath);

  const maturityPath = emitMaturityVector(cor);
  readJsonInput<MaturityVector>(maturityPath);

  const governancePath = emitGovernanceReceipt(cor, analysis, {
    steward: options?.steward,
    scope: options?.scope,
    hygiene,
  });
  const governance = readJsonInput<GovernanceReceipt>(governancePath);
  const csrPath = emitCsr(car, governance);

  return {
    hygiene,
    corPath,
    pgiPath,
    draPath,
    csrPath,
    analysisPath,
    maturityPath,
    governancePath,
    governance,
  };
}

export { hygienePasses, scanRepoHygiene };
