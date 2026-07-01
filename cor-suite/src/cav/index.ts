/**
 * CAV-1.0 public API — validate canonical registry integrity.
 */
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "../paths.js";
import type { CarRegistry } from "../types/car.js";
import type { CavReport, CavReportEntry } from "../types/cav.js";
import { loadCarRegistry } from "../car/registry.js";
import { writeJsonOutput } from "../lib/io.js";
import { COR_SUITE_PATHS } from "../paths.js";
import {
  cavPasses,
  emitCavValidation,
  validateCarRegistry,
} from "../car/validate.js";

export type { CavReport, CavReportEntry, CavValidationResult, CavFinding } from "../types/cav.js";
export { cavPasses, emitCavValidation, validateCarRegistry };

function hashFile(buf: Buffer): string {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

/** Core CAV checks: path existence and hash integrity per artifact. */
export function runCav(car: CarRegistry): CavReport {
  const blocking: CavReportEntry[] = [];
  const advisory: CavReportEntry[] = [];

  for (const artifact of car.artifacts) {
    const fullPath = path.join(REPO_ROOT, artifact.path.replace(/\\/g, "/"));

    if (!fs.existsSync(fullPath)) {
      blocking.push({
        id: artifact.id,
        issue: "missing_artifact",
        detail: `Path not found: ${artifact.path}`,
      });
      continue;
    }

    const buf = fs.readFileSync(fullPath);
    const hash = hashFile(buf);

    if (hash !== artifact.hash) {
      blocking.push({
        id: artifact.id,
        issue: "hash_mismatch",
        detail: `Expected ${artifact.hash}, got ${hash}`,
      });
    }

    if (artifact.status === "deprecated" && !artifact.links?.supersededBy?.length) {
      advisory.push({
        id: artifact.id,
        issue: "deprecated_without_successor",
        detail: `Deprecated artifact ${artifact.id} has no supersededBy link`,
      });
    }
  }

  return {
    cavVersion: "1.0.0",
    generatedAt: new Date().toISOString(),
    blocking,
    advisory,
  };
}

export function runCavFromDisk(): CavReport {
  return runCav(loadCarRegistry());
}

export function runCavFull(car?: CarRegistry) {
  return validateCarRegistry(car);
}

export function emitCavReport(car?: CarRegistry): string {
  const registry = car ?? loadCarRegistry();
  const report = runCav(registry);
  return writeJsonOutput(COR_SUITE_PATHS.outputs.cavReport, report);
}
