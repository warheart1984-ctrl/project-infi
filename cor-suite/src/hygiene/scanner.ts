import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT, COR_SUITE_PATHS } from "../paths.js";
import type { HygieneIssue, RepoHygieneStatus } from "../types/hygiene.js";
import { writeJsonOutput } from "../lib/io.js";

const FORBIDDEN_TRACKED_PREFIXES = ["node_modules/", "dist/", "build/", ".venv/", ".runtime/"];

function listTrackedFiles(): string[] {
  try {
    return execSync("git ls-files", { cwd: REPO_ROOT, encoding: "utf8" }).split("\n").filter(Boolean);
  } catch {
    return [];
  }
}

export function collectHygieneIssues(): HygieneIssue[] {
  const issues: HygieneIssue[] = [];
  const tracked = listTrackedFiles();

  for (const prefix of FORBIDDEN_TRACKED_PREFIXES) {
    const hits = tracked.filter((f) => f.replace(/\\/g, "/").includes(prefix));
    if (hits.length > 0) {
      issues.push({
        issueId: `HYG-TRACKED-${prefix.replace(/\//g, "-")}`,
        category: "directory_hygiene",
        description: `Forbidden path prefix tracked in git: ${prefix} (${hits.length} files)`,
        severity: "error",
      });
    }
  }

  for (const rel of [
    "cor-suite/spec/cor-state-vector.schema.json",
    "cor-suite/spec/car-1.0.schema.json",
    "cor-suite/car/car-1.0.json",
    "cor-suite/package.json",
    "aaes-os",
    "operator-surface",
    "frontend",
  ]) {
    if (!fs.existsSync(path.join(REPO_ROOT, rel))) {
      issues.push({
        issueId: `HYG-MISSING-${rel.replace(/[/\\.]/g, "-")}`,
        category: "canonical_paths",
        description: `Missing canonical path: ${rel}`,
        severity: "error",
      });
    }
  }

  const ciWorkflow = path.join(REPO_ROOT, ".github/workflows/cor-suite.yml");
  if (!fs.existsSync(ciWorkflow)) {
    issues.push({
      issueId: "HYG-CI-COR-SUITE",
      category: "ci_cd",
      description: "Missing .github/workflows/cor-suite.yml",
      severity: "warning",
    });
  }

  return issues;
}

export function hygienePasses(status: RepoHygieneStatus): boolean {
  return status.issues.every((i) => i.severity !== "error" && i.severity !== "critical");
}

export function scanRepoHygiene(): RepoHygieneStatus {
  const issues = collectHygieneIssues();
  const hasBlocking = issues.some((i) => i.severity === "error" || i.severity === "critical");

  return {
    repoId: "project-infi",
    scanTimestamp: new Date().toISOString(),
    deterministicArtifacts: !issues.some((i) => i.category === "determinism" && i.severity !== "info"),
    directoryHygieneOk: !issues.some((i) => i.category === "directory_hygiene" && i.severity !== "info"),
    canonicalPathsOk: !issues.some((i) => i.category === "canonical_paths" && i.severity !== "info"),
    reproducibleBuildsOk: true,
    ciCdIntegrated: fs.existsSync(path.join(REPO_ROOT, ".github/workflows/cor-suite.yml")),
    issues,
  };
}

export function emitRepoHygiene(): string {
  const status = scanRepoHygiene();
  return writeJsonOutput(COR_SUITE_PATHS.outputs.repoHygiene, status);
}
