import type { CarRegistry } from "../types/car.js";
import type { CsrReport } from "../types/csr.js";
import type { GovernanceReceipt } from "../types/governance.js";
import { writeJsonOutput, readJsonInput } from "../lib/io.js";
import { COR_SUITE_PATHS } from "../paths.js";
import { loadCarRegistry } from "../car/registry.js";
import fs from "node:fs";

function loadLatestReceipt(): GovernanceReceipt | undefined {
  try {
    if (fs.existsSync(COR_SUITE_PATHS.outputs.governanceReceipt)) {
      return readJsonInput<GovernanceReceipt>(COR_SUITE_PATHS.outputs.governanceReceipt);
    }
  } catch {
    /* optional */
  }
  return undefined;
}

/** CSR-1.0: stewardship participation and decision coverage from CAR + receipt. */
export function computeCsr(car: CarRegistry, receipt?: GovernanceReceipt): CsrReport {
  const receiptArtifacts = car.artifacts.filter((a) => a.kind === "governance_receipt");
  const requirements = car.artifacts.filter(
    (a) => a.kind === "requirement" && a.status === "active",
  );

  const stewards = new Set<string>();
  if (receipt?.steward) stewards.add(receipt.steward);

  const requirementsWithGovernanceLink = requirements.filter((r) =>
    car.artifacts.some(
      (a) =>
        a.links?.related?.includes(r.id) ||
        (a.kind === "governance_receipt" && a.namespace === r.namespace),
    ),
  ).length;

  const total = requirements.length;
  const coverageRatio = total > 0 ? requirementsWithGovernanceLink / total : 1;

  return {
    csrVersion: "1.0.0",
    generatedAt: new Date().toISOString(),
    stewardParticipation: {
      registeredReceipts: Math.max(receiptArtifacts.length, receipt ? 1 : 0),
      uniqueStewards: Math.max(stewards.size, receipt ? 1 : 0),
    },
    governanceActivity: {
      activeRequirements: total,
      governanceArtifacts: receiptArtifacts.length,
    },
    decisionCoverage: {
      requirementsTotal: total,
      requirementsWithGovernanceLink,
      coverageRatio,
    },
  };
}

export function emitCsr(car?: CarRegistry, receipt?: GovernanceReceipt): string {
  const registry = car ?? loadCarRegistry();
  const govReceipt = receipt ?? loadLatestReceipt();
  const report = computeCsr(registry, govReceipt);
  return writeJsonOutput(COR_SUITE_PATHS.outputs.csrReport, report);
}
