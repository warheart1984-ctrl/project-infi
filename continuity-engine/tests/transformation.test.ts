import { test } from "node:test";
import assert from "node:assert/strict";
import { realityToTruth } from "../src/transformation/truth";

test("reality → truth transformation", () => {
  const truth = realityToTruth({ observations: [] }, "nothing happened", []);
  assert.equal(truth.claim, "nothing happened");
});
