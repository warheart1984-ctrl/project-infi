#!/usr/bin/env node
/**
 * CI gate — exit 1 on hygiene failure, structural integrity, critical claims, or reject/freeze.
 */
import { COR_SUITE_PATHS } from "../paths.js";
import { readJsonInput } from "../lib/io.js";
import { hygienePasses } from "../hygiene/scanner.js";
import type { CorStateVector } from "../types/cor.js";
import type { ProofAnalysisResult } from "../types/analysis.js";
import type { GovernanceReceipt } from "../types/governance.js";
import type { RepoHygieneStatus } from "../types/hygiene.js";

import type { CavValidationResult } from "../types/cav.js";

function fail(msg: string): never {
  console.error(`COR Suite CI gate: ${msg}`);
  process.exit(1);
}

const cav = readJsonInput<CavValidationResult>(COR_SUITE_PATHS.outputs.cavValidation);
if (!cav.valid) {
  fail(`CAV-1.0 failed (${cav.blockingCount} blocking findings)`);
}

const hygiene = readJsonInput<RepoHygieneStatus>(COR_SUITE_PATHS.outputs.repoHygiene);
if (!hygienePasses(hygiene)) {
  fail(`hygiene failed (${hygiene.issues.length} issues)`);
}

const cor = readJsonInput<CorStateVector>(COR_SUITE_PATHS.outputs.corState);
if (cor.structuralIntegrity.brokenLineage.some((b) => b.issueType === "critical")) {
  fail("COR structural integrity: critical broken lineage");
}

const analysis = readJsonInput<ProofAnalysisResult>(COR_SUITE_PATHS.outputs.proofAnalysis);
const criticalClaims = analysis.claims.filter((c) => c.severity === "critical");
if (criticalClaims.length > 0) {
  fail(`${criticalClaims.length} critical proof analysis claims`);
}

const receipt = readJsonInput<GovernanceReceipt>(COR_SUITE_PATHS.outputs.governanceReceipt);
if (receipt.decision === "reject" || receipt.decision === "freeze") {
  fail(`governance decision is ${receipt.decision}`);
}

console.log(`COR Suite CI gate passed (decision=${receipt.decision})`);
