import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const TARGET_FILES = [
  "../server/veil-channel.mirror.ts",
] as const;

test("attunement enforcement paths stay non-instructional and bounded", async () => {
  for (const relativePath of TARGET_FILES) {
    const fileUrl = new URL(relativePath, import.meta.url);
    const source = await readFile(fileUrl, "utf8");

    assert.match(
      source,
      /function resolveUltraLowAttunementReply\(/,
      `${relativePath} must keep ultra-low attunement override.`,
    );
    assert.match(
      source,
      /mode:\s*"attunement-ultra-low"/,
      `${relativePath} must keep attunement ultra-low completion mode.`,
    );
    assert.match(
      source,
      /selectFirstContactReply\(/,
      `${relativePath} must keep a deterministic first-contact reply path for ultra-low arrival utterances.`,
    );
    assert.match(
      source,
      /if \(field\.gate === "sealed"\)\s*\{[\s\S]{0,240}?reply:\s*""/,
      `${relativePath} sealed branch must remain silent.`,
    );
    assert.ok(
      !source.includes("Add one concrete line and resend."),
      `${relativePath} must not instruct the user to rewrite the prompt.`,
    );
    assert.ok(
      !source.includes("buildWhisper(SPIRAL_SILENCE_MESSAGE"),
      `${relativePath} must not emit textual silence messages on enforcement paths.`,
    );
  }
});
