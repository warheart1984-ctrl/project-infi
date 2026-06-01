import assert from "node:assert/strict";
import test from "node:test";
import {
  isMemoryMode,
  nextMemoryMode,
  normalizeMemoryMode,
  resolveMemoryModeFromProviderSettings,
} from "../shared/memory-mode";

test("normalizeMemoryMode falls back to sigil-bound on unknown values", () => {
  assert.equal(normalizeMemoryMode("unknown"), "sigil-bound");
  assert.equal(normalizeMemoryMode(undefined, "open"), "open");
});

test("explicit provider memory mode takes precedence over legacy toggles", () => {
  const mode = resolveMemoryModeFromProviderSettings({
    memoryMode: "open",
    temporaryChatEnabled: true,
    memoryEnabled: false,
  });
  assert.equal(mode, "open");
});

test("legacy temporary or disabled memory resolves to sealed", () => {
  assert.equal(
    resolveMemoryModeFromProviderSettings({ temporaryChatEnabled: true }, "open"),
    "sealed",
  );
  assert.equal(
    resolveMemoryModeFromProviderSettings({ memoryEnabled: false }, "open"),
    "sealed",
  );
});

test("legacy history disabled resolves to sigil-bound", () => {
  const mode = resolveMemoryModeFromProviderSettings(
    { memoryEnabled: true, historyReferenceEnabled: false },
    "open",
  );
  assert.equal(mode, "sigil-bound");
});

test("nextMemoryMode cycles through triad in order", () => {
  assert.equal(nextMemoryMode("open"), "sigil-bound");
  assert.equal(nextMemoryMode("sigil-bound"), "sealed");
  assert.equal(nextMemoryMode("sealed"), "open");
});

test("isMemoryMode accepts only triad values", () => {
  assert.equal(isMemoryMode("open"), true);
  assert.equal(isMemoryMode("sigil-bound"), true);
  assert.equal(isMemoryMode("sealed"), true);
  assert.equal(isMemoryMode("balanced"), false);
});
