import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("chat window renders a deliberate silence pulse for empty assistant content", async () => {
  const fileUrl = new URL("../client/src/components/chat-window.tsx", import.meta.url);
  const source = await readFile(fileUrl, "utf8");

  assert.match(
    source,
    /function isSilentAssistantMessage\(message: Message\): boolean/,
    "chat window should classify silent assistant messages explicitly.",
  );
  assert.match(
    source,
    /isSilentAssistantMessage\(message\)\s*\?/,
    "chat window should branch away from standard message bubble rendering for silent assistant content.",
  );
  assert.match(
    source,
    /data-testid=\{`text-veil-silence-pulse-\$\{message\.id\}`\}/,
    "chat window should render a dedicated silence pulse marker.",
  );
  assert.ok(
    !source.includes("add one concrete action request"),
    "chat window must not include concrete-action instruction leakage.",
  );
});

test("veil channels treat terminal empty output as valid completion", async () => {
  const targets = [
    "../server/veil-channel.mirror.ts",
  ] as const;

  for (const relativePath of targets) {
    const fileUrl = new URL(relativePath, import.meta.url);
    const source = await readFile(fileUrl, "utf8");

    assert.match(
      source,
      /Promise<\{ reply: string; terminalEmpty: boolean \}>/,
      `${relativePath} generateModelReply should propagate terminalEmpty metadata.`,
    );
    assert.match(
      source,
      /terminalEmpty: true/,
      `${relativePath} should mark enforcement empty outputs as terminal.`,
    );
    assert.match(
      source,
      /terminalEmptyFromProvider/,
      `${relativePath} should carry terminal-empty state through caller aggregation.`,
    );
    assert.match(
      source,
      /allowBlankReply[\s\S]{0,180}terminalEmptyFromProvider/,
      `${relativePath} should allow empty terminal replies without fallback substitution.`,
    );
  }
});
