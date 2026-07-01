#!/usr/bin/env node
import { emitCorState, validateAndEmitCav } from "../cor/index.js";
import { emitProofAnalysis } from "../analysis/index.js";
import { emitGovernanceReceipt } from "../governance/engine.js";
import { emitMaturityVector } from "../maturity/index.js";
import { emitRepoHygiene, hygienePasses, scanRepoHygiene } from "../hygiene/scanner.js";
import { runCorSuitePipeline } from "../hygiene/pipeline.js";
import { bootstrapCarRegistry } from "../car/bootstrap.js";
import { cavPasses, emitCavValidation } from "../car/validate.js";
import { emitCavReport } from "../cav/index.js";
import { emitPgi } from "../pgi/index.js";
import { emitDra } from "../dra/index.js";
import { emitCsr } from "../csr/index.js";
import { carRegistryExists, loadCarRegistry } from "../car/registry.js";
import { readJsonInput } from "../lib/io.js";
import { COR_SUITE_PATHS } from "../paths.js";
import type { CorStateVector } from "../types/cor.js";
import type { ProofAnalysisResult } from "../types/analysis.js";
import type { RepoHygieneStatus } from "../types/hygiene.js";

async function main(): Promise<void> {
  const cmd = process.argv[2];

  switch (cmd) {
    case "hygiene": {
      const path = emitRepoHygiene();
      const status = readJsonInput<RepoHygieneStatus>(path);
      console.log(JSON.stringify(status, null, 2));
      if (!hygienePasses(status)) process.exitCode = 1;
      break;
    }
    case "car": {
      if (!carRegistryExists()) {
        console.error(`CAR registry missing at ${COR_SUITE_PATHS.carRegistry}`);
        process.exitCode = 1;
        break;
      }
      const registry = loadCarRegistry();
      console.log(
        JSON.stringify(
          {
            carVersion: registry.carVersion,
            generatedAt: registry.generatedAt,
            artifactCount: registry.artifacts.length,
            path: COR_SUITE_PATHS.carRegistry,
          },
          null,
          2,
        ),
      );
      break;
    }
    case "cav":
    case "validate": {
      const result = emitCavValidation();
      emitCavReport();
      console.log(JSON.stringify(result, null, 2));
      if (!cavPasses(result)) process.exitCode = 1;
      break;
    }
    case "pgi": {
      const path = emitPgi();
      console.log(`PGI → ${path}`);
      break;
    }
    case "dra": {
      const path = emitDra();
      console.log(`DRA report → ${path}`);
      break;
    }
    case "csr": {
      const path = emitCsr();
      console.log(`CSR report → ${path}`);
      break;
    }
    case "car-bootstrap": {
      const registry = await bootstrapCarRegistry();
      console.log(`CAR registry → ${COR_SUITE_PATHS.carRegistry} (${registry.artifacts.length} artifacts)`);
      break;
    }
    case "cor": {
      const path = await emitCorState();
      const car = loadCarRegistry();
      emitPgi(car);
      emitDra(car);
      emitCsr(car);
      console.log(`COR state vector → ${path}`);
      break;
    }
    case "analyze": {
      const cor = readJsonInput<CorStateVector>(COR_SUITE_PATHS.outputs.corState);
      const path = emitProofAnalysis(cor);
      console.log(`Proof Analysis → ${path}`);
      break;
    }
    case "maturity": {
      const path = emitMaturityVector();
      console.log(`Maturity vector → ${path}`);
      break;
    }
    case "govern": {
      const cor = readJsonInput<CorStateVector>(COR_SUITE_PATHS.outputs.corState);
      const analysis = readJsonInput<ProofAnalysisResult>(COR_SUITE_PATHS.outputs.proofAnalysis);
      let hygiene: RepoHygieneStatus | undefined;
      if (COR_SUITE_PATHS.outputs.repoHygiene) {
        try {
          hygiene = readJsonInput<RepoHygieneStatus>(COR_SUITE_PATHS.outputs.repoHygiene);
        } catch {
          hygiene = scanRepoHygiene();
        }
      }
      const path = emitGovernanceReceipt(cor, analysis, { hygiene, steward: "cor-suite-cli" });
      console.log(`Governance receipt → ${path}`);
      break;
    }
    case "pipeline": {
      const result = await runCorSuitePipeline({ steward: "cor-suite-cli" });
      console.log(JSON.stringify({ governance: result.governance.decision, paths: result }, null, 2));
      if (!hygienePasses(result.hygiene)) process.exitCode = 1;
      if (["reject", "freeze"].includes(result.governance.decision)) process.exitCode = 1;
      break;
    }
    default:
      console.error(
        "Usage: cor-suite [hygiene|car|cav|validate|car-bootstrap|cor|pgi|dra|csr|analyze|maturity|govern|pipeline]",
      );
      process.exitCode = 1;
  }
}

main().catch((err: unknown) => {
  console.error(err instanceof Error ? err.message : err);
  process.exitCode = 1;
});
