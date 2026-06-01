import assert from "node:assert/strict";
import test from "node:test";
import { buildGlyphMemory } from "../server/memory/glyph";
import { invokeSpiralProcess, type InvocationContext } from "../server/spiral-process";

function buildContext(overrides?: Partial<InvocationContext>): InvocationContext {
  return {
    input: "Unit test invocation",
    trace: "trace: unit-test",
    seal: "VOW-BOUND",
    echo: "intent:utterance",
    memoryMode: "open",
    memory: [],
    responseShape: {
      tone: "direct",
      style: "plain",
    },
    field: {
      tone: "void",
      mirror: "voice",
      gate: "open",
      sigils: [],
      presenceLevel: 0.86,
      memoryMode: "open",
      distortions: [],
      trace: "trace: unit-test",
    },
    voices: ["seer"],
    ...overrides,
  };
}

async function runMemoryPhase(context: InvocationContext): Promise<Record<string, unknown>> {
  const result = await invokeSpiralProcess(context, async () => "ok");
  const memoryPhase = result.phases.find((phase) => phase.id === "memory");
  assert.ok(memoryPhase, "Expected memory phase to exist.");
  return memoryPhase.payload;
}

test("memory phase marks trace as present for local seeds", async () => {
  const payload = await runMemoryPhase(
    buildContext({
      memory: [
        buildGlyphMemory({
          utterance: "Local thread memory",
          trace: "trace: open-history source:conversation",
          seal: "VOW-BOUND",
          presenceScore: 0.58,
        }),
      ],
    }),
  );

  assert.equal(payload.traceState, "present");
  assert.equal(payload.seededCount, 1);
  assert.equal(payload.importedSeedCount, 0);
});

test("memory phase marks trace as imported when imported seeds exist", async () => {
  const payload = await runMemoryPhase(
    buildContext({
      memory: [
        buildGlyphMemory({
          utterance: "Imported seed",
          trace: "trace: open-history source:imported-conversation",
          seal: "VOW-BOUND",
          presenceScore: 0.58,
        }),
        buildGlyphMemory({
          utterance: "Current thread memory",
          trace: "trace: open-history source:conversation",
          seal: "VOW-BOUND",
          presenceScore: 0.58,
        }),
      ],
    }),
  );

  assert.equal(payload.traceState, "imported");
  assert.equal(payload.seededCount, 2);
  assert.equal(payload.importedSeedCount, 1);
});

test("memory phase marks trace as none when no seeds are available", async () => {
  const payload = await runMemoryPhase(buildContext({ memory: [] }));

  assert.equal(payload.traceState, "none");
  assert.equal(payload.seededCount, 0);
  assert.equal(payload.importedSeedCount, 0);
});

test("memory phase stays sealed when memory mode is sealed", async () => {
  const payload = await runMemoryPhase(
    buildContext({
      memoryMode: "sealed",
      field: {
        tone: "void",
        mirror: "voice",
        gate: "sealed",
        sigils: [],
        presenceLevel: 0.2,
        memoryMode: "sealed",
        distortions: [],
        trace: "trace: unit-test",
      },
      memory: [
        buildGlyphMemory({
          utterance: "Seed that should remain sealed",
          trace: "trace: open-history source:conversation",
          seal: "VOW-BOUND",
          presenceScore: 0.58,
        }),
      ],
    }),
  );

  assert.equal(payload.traceState, "sealed");
  assert.equal(payload.seededCount, 1);
});
