import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { DanielModule } from "../src/modules/daniel/module.js";
import type { AAESAction } from "../src/types.js";

describe("DanielModule", () => {
  const daniel = new DanielModule();

  it("handles daniel.* and code.* targets", () => {
    const actions: AAESAction[] = [
      { actionId: "a1", target: "daniel", operation: "code", args: {} },
      { actionId: "a2", target: "daniel.code", operation: "execute", args: {} },
      { actionId: "a3", target: "code", operation: "write", args: {} },
    ];
    for (const action of actions) {
      assert.equal(daniel.canHandle(action), true);
    }
  });

  it("returns simulated success with diff", async () => {
    const result = await daniel.execute({
      actionId: "a1",
      target: "daniel",
      operation: "code",
      args: { description: "patch" },
    });
    assert.equal(result.status, "success");
    assert.ok(result.output && typeof result.output === "object");
    const output = result.output as Record<string, unknown>;
    assert.equal(output.status, "success");
    assert.match(String(output.diff), /\+\+\+ b\//);
  });

  it("does not handle unrelated targets", () => {
    assert.equal(
      daniel.canHandle({ actionId: "x", target: "network", operation: "fetch", args: {} }),
      false,
    );
  });
});
