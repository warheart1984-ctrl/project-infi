import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { COR_SUITE_PATHS, REPO_ROOT } from "../paths.js";

export function ensureOutputDir(): void {
  fs.mkdirSync(COR_SUITE_PATHS.outputDir, { recursive: true });
}

export function writeJsonOutput(filePath: string, data: unknown): string {
  ensureOutputDir();
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  return filePath;
}

export function readJsonInput<T>(filePath: string): T {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Missing required artifact: ${filePath}`);
  }
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

export function tryGitCommit(): string | undefined {
  try {
    return execSync("git rev-parse HEAD", {
      cwd: REPO_ROOT,
      encoding: "utf8",
    }).trim();
  } catch {
    return undefined;
  }
}
