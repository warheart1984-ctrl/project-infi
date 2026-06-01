import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, mkdir, rm, writeFile } from "fs/promises";
import { tmpdir } from "os";
import path from "path";
import {
  buildSelfInspectionIndex,
  formatSelfInspectionQuery,
  formatSelfInspectionSummary,
  querySelfInspection,
} from "../server/self-inspection";

async function withTempWorkspace<T>(run: (workspaceRoot: string) => Promise<T>): Promise<T> {
  const workspaceRoot = await mkdtemp(path.join(tmpdir(), "spiral-self-inspect-"));
  try {
    return await run(workspaceRoot);
  } finally {
    await rm(workspaceRoot, { recursive: true, force: true });
  }
}

test("buildSelfInspectionIndex indexes exports and comments from configured roots", async () => {
  await withTempWorkspace(async (workspaceRoot) => {
    const serverDir = path.join(workspaceRoot, "server");
    await mkdir(serverDir, { recursive: true });
    await writeFile(
      path.join(serverDir, "entry.ts"),
      [
        "// auth entry point",
        "import { readFile } from \"fs/promises\";",
        "",
        "export interface AuthState {",
        "  token: string;",
        "}",
        "",
        "export async function enforceAuth(): Promise<boolean> {",
        "  return true;",
        "}",
        "",
        "export const wakeRigAgents = (): void => {};",
        "",
      ].join("\n"),
      "utf8",
    );

    const index = await buildSelfInspectionIndex({
      rootDir: workspaceRoot,
      includeDirs: ["server"],
    });

    assert.equal(index.fileCount, 1);
    assert.equal(index.files[0].path, "server/entry.ts");
    assert.equal(index.gitCommit, null);
    assert.ok(index.symbolCount >= 3);
    assert.ok(index.files[0].comments.some((comment) => comment.includes("auth entry point")));
    assert.ok(index.files[0].exports.some((entry) => entry.name === "enforceAuth"));
    assert.ok(index.files[0].exports.some((entry) => entry.name === "wakeRigAgents"));
    assert.ok(index.files[0].exports.some((entry) => entry.name === "AuthState"));

    const summary = formatSelfInspectionSummary(index);
    assert.match(summary, /Indexed files: 1/);
  });
});

test("querySelfInspection returns structural matches for symbol and comment queries", async () => {
  await withTempWorkspace(async (workspaceRoot) => {
    const serverDir = path.join(workspaceRoot, "server");
    await mkdir(serverDir, { recursive: true });
    await writeFile(
      path.join(serverDir, "trace.ts"),
      [
        "// memory persistence guard",
        "export function wakeRigAgents(): string {",
        "  return \"ok\";",
        "}",
        "",
      ].join("\n"),
      "utf8",
    );

    const symbolResult = await querySelfInspection("wakeRigAgents", {
      rootDir: workspaceRoot,
      includeDirs: ["server"],
      forceRefresh: true,
      limit: 10,
    });
    assert.ok(symbolResult.totalMatches >= 1);
    assert.ok(symbolResult.matches.some((match) => match.label.includes("wakeRigAgents")));

    const commentResult = await querySelfInspection("memory persistence", {
      rootDir: workspaceRoot,
      includeDirs: ["server"],
      forceRefresh: true,
      limit: 10,
    });
    assert.ok(commentResult.totalMatches >= 1);
    assert.ok(commentResult.matches.some((match) => match.kind === "comment"));

    const formatted = formatSelfInspectionQuery(symbolResult);
    assert.match(formatted, /Self-inspection matches/);
    assert.match(formatted, /server\/trace.ts/);
  });
});
