import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { DefaultInvariantEngine } from "../src/engines/invariant_engine.js";
import type { AAESContext } from "../src/types.js";

function baseCtx(overrides: Partial<AAESContext> = {}): AAESContext {
  return {
    traceId: "trace_test",
    request: {
      actorId: "operator-1",
      scope: { name: "dev", resources: [] },
      payload: { prompt: "hello" },
    },
    session: {},
    steps: [],
    metadata: {},
    ...overrides,
  };
}

describe("DefaultInvariantEngine", () => {
  const engine = new DefaultInvariantEngine();

  it("allows valid context", () => {
    const result = engine.evaluate(baseCtx());
    assert.equal(result.allowed, true);
    assert.equal(result.violations.length, 0);
  });

  it("blocks missing actorId", () => {
    const ctx = baseCtx({
      request: { actorId: "", scope: { name: "dev" } },
    });
    const result = engine.evaluate(ctx);
    assert.equal(result.allowed, false);
    assert.ok(result.violations.some((v) => v.code === "AAES_IDENTITY_INVALID"));
  });

  it("blocks missing scope.name", () => {
    const ctx = baseCtx({
      request: { actorId: "op", scope: { name: "" } },
    });
    const result = engine.evaluate(ctx);
    assert.equal(result.allowed, false);
    assert.ok(result.violations.some((v) => v.code === "AAES_SCOPE_MISSING"));
  });

  it("requires traceId and timestamps on steps", () => {
    const ctx = baseCtx({ traceId: "" });
    const result = engine.evaluate(ctx, {
      stepId: "",
      stepType: "test",
      summary: "x",
      timestamp: "",
      status: "ok",
    });
    assert.equal(result.allowed, false);
    assert.ok(result.violations.length > 0);
  });
});
