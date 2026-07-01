import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT, COR_SUITE_PATHS } from "../paths.js";
import type { CarArtifact, CarArtifactKind, CarRegistry } from "../types/car.js";
import type { CavFinding, CavValidationResult } from "../types/cav.js";
import { loadCarRegistry } from "./registry.js";
import { writeJsonOutput } from "../lib/io.js";

const ARTIFACT_KINDS: CarArtifactKind[] = [
  "requirement",
  "specification",
  "implementation",
  "verification",
  "evidence",
  "governance_receipt",
  "schema",
  "registry",
];

const ARTIFACT_STATUSES = ["draft", "active", "deprecated", "retired"] as const;

function hashBuffer(buf: Buffer): string {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function validateCarShape(car: CarRegistry): CavFinding[] {
  const findings: CavFinding[] = [];

  if (!car.carVersion || typeof car.carVersion !== "string") {
    findings.push({
      findingId: "CAV-SCHEMA-VERSION",
      category: "schema",
      severity: "critical",
      message: "carVersion is required and must be a string",
      blocking: true,
    });
  }
  if (!car.generatedAt || typeof car.generatedAt !== "string") {
    findings.push({
      findingId: "CAV-SCHEMA-GENERATED",
      category: "schema",
      severity: "critical",
      message: "generatedAt is required and must be a string",
      blocking: true,
    });
  }
  if (!Array.isArray(car.artifacts)) {
    findings.push({
      findingId: "CAV-SCHEMA-ARTIFACTS",
      category: "schema",
      severity: "critical",
      message: "artifacts must be an array",
      blocking: true,
    });
    return findings;
  }

  for (const [i, artifact] of car.artifacts.entries()) {
    const prefix = `CAV-SCHEMA-${i}`;
    for (const field of ["id", "namespace", "kind", "version", "status", "path", "hash"] as const) {
      if (!artifact[field] || typeof artifact[field] !== "string") {
        findings.push({
          findingId: `${prefix}-${field}`,
          category: "schema",
          severity: "critical",
          artifactId: artifact.id,
          message: `Artifact[${i}] missing required field: ${field}`,
          blocking: true,
        });
      }
    }
    if (artifact.kind && !ARTIFACT_KINDS.includes(artifact.kind)) {
      findings.push({
        findingId: `${prefix}-kind-enum`,
        category: "schema",
        severity: "critical",
        artifactId: artifact.id,
        message: `Invalid kind: ${artifact.kind}`,
        blocking: true,
      });
    }
    if (artifact.status && !ARTIFACT_STATUSES.includes(artifact.status)) {
      findings.push({
        findingId: `${prefix}-status-enum`,
        category: "schema",
        severity: "critical",
        artifactId: artifact.id,
        message: `Invalid status: ${artifact.status}`,
        blocking: true,
      });
    }
  }

  return findings;
}

function validateIntegrity(car: CarRegistry): CavFinding[] {
  const findings: CavFinding[] = [];
  const seenIds = new Map<string, number>();

  for (const artifact of car.artifacts) {
    const count = (seenIds.get(artifact.id) ?? 0) + 1;
    seenIds.set(artifact.id, count);
    if (count > 1) {
      findings.push({
        findingId: `CAV-DUP-${artifact.id}`,
        category: "duplicate_id",
        severity: "critical",
        artifactId: artifact.id,
        message: `Duplicate artifact id: ${artifact.id}`,
        blocking: true,
      });
    }

    const absPath = path.join(REPO_ROOT, artifact.path.replace(/\\/g, "/"));
    if (!fs.existsSync(absPath)) {
      findings.push({
        findingId: `CAV-MISSING-${artifact.id}`,
        category: "missing_path",
        severity: "error",
        artifactId: artifact.id,
        path: artifact.path,
        message: `Artifact path does not exist: ${artifact.path}`,
        blocking: true,
      });
      continue;
    }

    const buf = fs.readFileSync(absPath);
    const actualHash = hashBuffer(buf);
    if (actualHash !== artifact.hash) {
      findings.push({
        findingId: `CAV-HASH-${artifact.id}`,
        category: "hash_mismatch",
        severity: "error",
        artifactId: artifact.id,
        path: artifact.path,
        message: `Hash mismatch for ${artifact.path} (expected ${artifact.hash.slice(0, 12)}…, got ${actualHash.slice(0, 12)}…)`,
        blocking: true,
      });
    }
  }

  return findings;
}

function validateLifecycle(car: CarRegistry): CavFinding[] {
  const findings: CavFinding[] = [];
  const ids = new Set(car.artifacts.map((a) => a.id));

  for (const artifact of car.artifacts) {
    if (artifact.status === "deprecated") {
      if (!artifact.lifecycle?.deprecatedAt) {
        findings.push({
          findingId: `CAV-LC-DEP-${artifact.id}`,
          category: "lifecycle",
          severity: "warning",
          artifactId: artifact.id,
          message: `Deprecated artifact ${artifact.id} missing deprecatedAt`,
          blocking: false,
        });
      }
      if (!artifact.links?.supersededBy?.length) {
        findings.push({
          findingId: `CAV-LC-SUCC-${artifact.id}`,
          category: "advisory",
          severity: "warning",
          artifactId: artifact.id,
          message: `Deprecated artifact ${artifact.id} has no supersededBy link`,
          blocking: false,
        });
      }
    }
    if (artifact.status === "retired" && !artifact.lifecycle?.retiredAt) {
      findings.push({
        findingId: `CAV-LC-RET-${artifact.id}`,
        category: "lifecycle",
        severity: "error",
        artifactId: artifact.id,
        message: `Retired artifact ${artifact.id} missing retiredAt`,
        blocking: true,
      });
    }
    for (const ref of [
      ...(artifact.links?.supersedes ?? []),
      ...(artifact.links?.supersededBy ?? []),
      ...(artifact.links?.related ?? []),
    ]) {
      if (!ids.has(ref)) {
        findings.push({
          findingId: `CAV-LINK-${artifact.id}-${ref}`,
          category: "integrity",
          severity: "warning",
          artifactId: artifact.id,
          message: `Broken link from ${artifact.id} to unknown id ${ref}`,
          blocking: false,
        });
      }
    }
  }

  return findings;
}

export function validateCarRegistry(car?: CarRegistry): CavValidationResult {
  const registry = car ?? loadCarRegistry();
  const findings = [
    ...validateCarShape(registry),
    ...validateIntegrity(registry),
    ...validateLifecycle(registry),
  ];

  const blockingCount = findings.filter((f) => f.blocking).length;
  const advisoryCount = findings.filter((f) => !f.blocking).length;

  return {
    cavVersion: "1.0.0",
    carRef: COR_SUITE_PATHS.carRegistry,
    generatedAt: new Date().toISOString(),
    valid: blockingCount === 0,
    blockingCount,
    advisoryCount,
    findings,
  };
}

export function emitCavValidation(car?: CarRegistry): CavValidationResult {
  const result = validateCarRegistry(car);
  writeJsonOutput(COR_SUITE_PATHS.outputs.cavValidation, result);
  return result;
}

export function cavPasses(result: CavValidationResult): boolean {
  return result.valid;
}
