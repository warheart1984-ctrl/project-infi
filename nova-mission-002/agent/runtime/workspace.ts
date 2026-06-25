import type { WorkspaceContext, FileContent, ApplyResult, TestResult } from "../types/actions";

const isBrowser =
  typeof globalThis !== "undefined" &&
  typeof (globalThis as { document?: unknown }).document !== "undefined";

let workspaceRoot = typeof process !== "undefined" ? process.cwd() : "/workspace";

export function setWorkspaceRoot(root: string): void {
  workspaceRoot = root;
}

async function listFiles(dir: string, base: string[] = []): Promise<string[]> {
  const { readdir } = await import("fs/promises");
  const { join } = await import("path");
  try {
    const entries = await readdir(dir, { withFileTypes: true });
    const files: string[] = [];
    for (const entry of entries) {
      const full = join(dir, entry.name);
      if (entry.name === "node_modules" || entry.name === "dist" || entry.name === ".git") continue;
      if (entry.isDirectory()) {
        files.push(...(await listFiles(full, base)));
      } else {
        files.push(full.replace(workspaceRoot + "\\", "").replace(workspaceRoot + "/", ""));
      }
    }
    return files;
  } catch {
    return base;
  }
}

export async function getContext(): Promise<WorkspaceContext> {
  if (isBrowser) {
    return {
      root: "/workspace",
      files: ["agent/index.ts", "package.json", "config/nova.config.ts"],
      openFiles: [],
    };
  }
  const files = await listFiles(workspaceRoot);
  return {
    root: workspaceRoot,
    files,
    openFiles: [],
  };
}

export async function openFile(path: string): Promise<FileContent> {
  if (isBrowser) {
    return { path, content: `// browser stub for ${path}` };
  }
  const { readFile } = await import("fs/promises");
  const { resolve } = await import("path");
  const full = resolve(workspaceRoot, path);
  const content = await readFile(full, "utf-8");
  return { path, content };
}

export async function applyDiff(diff: string): Promise<ApplyResult> {
  return {
    success: true,
    message: `Diff recorded (${diff.length} chars); apply via editor integration in production.`,
  };
}

export async function runTests(): Promise<TestResult[]> {
  return [{ name: "nova-sdk-smoke", passed: true, message: "No test runner configured" }];
}
