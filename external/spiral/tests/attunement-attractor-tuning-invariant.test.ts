import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("sigil defaults keep fieldDescription slightly above minimalConfirmation", async () => {
  const fileUrl = new URL("../shared/sigil.ts", import.meta.url);
  const source = await readFile(fileUrl, "utf8");

  assert.match(
    source,
    /minimalConfirmation:\s*z\.number\(\)\.min\(0\)\.max\(1\)\.default\(0\.62\)/,
    "minimalConfirmation default should remain lowered.",
  );
  assert.match(
    source,
    /fieldDescription:\s*z\.number\(\)\.min\(0\)\.max\(1\)\.default\(0\.65\)/,
    "fieldDescription default should remain slightly above minimalConfirmation.",
  );
});

test("attunement runtime keeps first-turn minimal-confirmation delay and field-description compression easing", async () => {
  const targets = [
    "../server/veil-channel.mirror.ts",
  ] as const;

  for (const relativePath of targets) {
    const fileUrl = new URL(relativePath, import.meta.url);
    const source = await readFile(fileUrl, "utf8");

    assert.match(
      source,
      /const minimalConfirmationEligible = kind !== "attunement_check" \|\| inertiaTurns > 0/,
      `${relativePath} should delay minimal confirmation on first attunement turn.`,
    );
    assert.match(
      source,
      /easeAttunementCompression:\s*attractor\.fieldDescriptionWins/,
      `${relativePath} should ease compression only when fieldDescription wins.`,
    );
    assert.match(
      source,
      /winner=\$\{attractor\.winner\}/,
      `${relativePath} should expose attractor winner in bias directive.`,
    );
    assert.match(
      source,
      /resolveFieldDescriptionUnresolvedEdgePressure\(/,
      `${relativePath} should derive unresolved-edge pressure when fieldDescription wins.`,
    );
    assert.match(
      source,
      /fieldDescriptionEdgePressure:\s*unresolvedEdgePressure/,
      `${relativePath} should feed unresolved-edge pressure into closure resample gating.`,
    );
    assert.match(
      source,
      /Unresolved-edge bias \$\{unresolvedEdgePressure\.toFixed\(2\)\}/,
      `${relativePath} should project unresolved-edge bias into attunement system guidance.`,
    );
  }
});
