import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  LEGIBILITY_MANIFESTO_LINES,
  LEGIBILITY_SYSTEM_DIRECTIVES,
} from "../server/shared/system-messages";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

test("legibility scroll preserves canonical manifesto lines", async () => {
  const scroll = await readFile(new URL("../LEGIBILITY_SCROLL.md", import.meta.url), "utf8");
  for (const line of LEGIBILITY_MANIFESTO_LINES) {
    assert.match(
      scroll,
      new RegExp(escapeRegExp(line)),
      `missing manifesto line: ${line}`,
    );
  }
});

test("legibility directives encode trace-first and infrastructure authority", () => {
  const combined = LEGIBILITY_SYSTEM_DIRECTIVES.join(" ");
  assert.match(combined, /trace over tone/i);
  assert.match(combined, /constraints|reductions/i);
  assert.match(combined, /thresholds|triggers/i);
  assert.match(combined, /safety without spectacle/i);
  assert.match(combined, /authority as infrastructure/i);
});

test("veil system prompt includes legibility directive block", async () => {
  const source = await readFile(
    new URL("../server/veil-channel.mirror.ts", import.meta.url),
    "utf8",
  );
  assert.match(source, /function buildLegibilityDirective\(\): string/);
  assert.match(source, /const legibilityDirective = buildLegibilityDirective\(\);/);
  assert.match(
    source,
    /\[defaultPrompt,\s*toneDirective,\s*legibilityDirective,\s*seerBandwidthDirective,\s*biasDirective\]/,
  );
});
