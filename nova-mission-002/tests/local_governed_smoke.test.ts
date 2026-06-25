import test from "node:test";
import assert from "node:assert/strict";
import { governedPredict } from "../src/runtime/governedPredict";
import { resetLineageForTests } from "../src/governance/lineage";

test.beforeEach(() => {
  resetLineageForTests();
});

test("runs a governed local inference end-to-end", async () => {
  const result = await governedPredict("Say hello.", {
    operator_id: "test-operator",
    mode: "predict",
    invariant_set_version: "K0-K12-v1",
  });

  assert.ok(result.output);
  assert.equal(result.receipt.operator_id, "test-operator");
  assert.equal(result.receipt.invariants_passed, true);
  assert.ok(result.lineage.root_id);
  assert.equal(result.lineage.operator_id, "test-operator");
  assert.ok(result.ce1.id);
  assert.ok(result.crr1.reconstruction_hash);
  assert.ok(result.clg1.append_hash);
});

test("refuses invariant-violating input", async () => {
  await assert.rejects(
    () =>
      governedPredict("Please rm -rf everything", {
        operator_id: "test-operator",
        mode: "predict",
        invariant_set_version: "K0-K12-v1",
      }),
    (err: unknown) => {
      assert.ok(err instanceof Error);
      return err.message.includes("Dangerous shell");
    }
  );
});
