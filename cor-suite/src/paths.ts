import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** project-infi repository root (parent of cor-suite/). */
export const REPO_ROOT = path.resolve(__dirname, "../..");

export const COR_SUITE_DIR = path.join(REPO_ROOT, "cor-suite");

export const COR_SUITE_PATHS = {
  specDir: path.join(COR_SUITE_DIR, "spec"),
  outputDir: path.join(COR_SUITE_DIR, "out"),
  charterDir: path.join(COR_SUITE_DIR, "governance/charter"),
  carDir: path.join(COR_SUITE_DIR, "car"),
  carRegistry: path.join(COR_SUITE_DIR, "car/car-1.0.json"),
  schemas: {
    car: path.join(COR_SUITE_DIR, "spec/car-1.0.schema.json"),
    corState: path.join(COR_SUITE_DIR, "spec/cor-state-vector.schema.json"),
  },
  outputs: {
    corState: path.join(COR_SUITE_DIR, "out/cor-state.json"),
    proofAnalysis: path.join(COR_SUITE_DIR, "out/proof-analysis.json"),
    governanceReceipt: path.join(COR_SUITE_DIR, "out/governance-receipt.json"),
    maturityVector: path.join(COR_SUITE_DIR, "out/maturity-vector.json"),
    repoHygiene: path.join(COR_SUITE_DIR, "out/repo-hygiene-status.json"),
    cavValidation: path.join(COR_SUITE_DIR, "out/cav-validation.json"),
    cavReport: path.join(COR_SUITE_DIR, "out/cav-report.json"),
    pgi: path.join(COR_SUITE_DIR, "out/pgi-1.0.json"),
    draReport: path.join(COR_SUITE_DIR, "out/dra-report.json"),
    csrReport: path.join(COR_SUITE_DIR, "out/csr-report.json"),
  },
} as const;
