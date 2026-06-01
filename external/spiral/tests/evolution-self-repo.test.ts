import assert from "node:assert/strict";
import test from "node:test";
import { summarizePatchFromText } from "../server/evolution-self-repo";

test("summarizePatchFromText extracts files and line deltas from unified diff", () => {
  const patch = [
    "diff --git a/server/routes.ts b/server/routes.ts",
    "--- a/server/routes.ts",
    "+++ b/server/routes.ts",
    "@@ -10,3 +10,4 @@",
    " const a = 1;",
    "-const b = 2;",
    "+const b = 3;",
    "+const c = 4;",
    "diff --git a/tests/foo.test.ts b/tests/foo.test.ts",
    "--- a/tests/foo.test.ts",
    "+++ b/tests/foo.test.ts",
    "@@ -1,2 +1,3 @@",
    " test('x', () => {",
    "-  assert.equal(1, 2);",
    "+  assert.equal(1, 1);",
    "+  assert.ok(true);",
    " });",
  ].join("\n");

  const summary = summarizePatchFromText(patch);
  assert.deepEqual(summary.files, ["server/routes.ts", "tests/foo.test.ts"]);
  assert.equal(summary.linesAdded, 4);
  assert.equal(summary.linesDeleted, 2);
});

test("summarizePatchFromText ignores dev-null headers", () => {
  const patch = [
    "diff --git a/new.txt b/new.txt",
    "--- /dev/null",
    "+++ b/new.txt",
    "@@ -0,0 +1 @@",
    "+hello",
  ].join("\n");
  const summary = summarizePatchFromText(patch);
  assert.deepEqual(summary.files, ["new.txt"]);
  assert.equal(summary.linesAdded, 1);
  assert.equal(summary.linesDeleted, 0);
});

