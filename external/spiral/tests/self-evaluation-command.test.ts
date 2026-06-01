import assert from "node:assert/strict";
import test from "node:test";
import { parseSelfEvaluationCommand } from "../server/self-evaluation-command";

test("parseSelfEvaluationCommand resolves default integrity profile", () => {
  assert.deepEqual(parseSelfEvaluationCommand("self evaluate"), { profile: "integrity" });
  assert.deepEqual(parseSelfEvaluationCommand("self evaluate."), { profile: "integrity" });
  assert.deepEqual(parseSelfEvaluationCommand("please self evaluate"), { profile: "integrity" });
});

test("parseSelfEvaluationCommand resolves explicit profiles", () => {
  assert.deepEqual(parseSelfEvaluationCommand("self evaluate integrity"), { profile: "integrity" });
  assert.deepEqual(parseSelfEvaluationCommand("self evaluate gates"), { profile: "gates" });
  assert.deepEqual(parseSelfEvaluationCommand("self evaluate contracts"), { profile: "contracts" });
  assert.deepEqual(parseSelfEvaluationCommand("self evaluate all"), { profile: "all" });
});

test("parseSelfEvaluationCommand ignores unrelated and invalid profiles", () => {
  assert.equal(parseSelfEvaluationCommand("self inspect"), undefined);
  assert.equal(parseSelfEvaluationCommand("self evaluate unknown"), undefined);
  assert.equal(parseSelfEvaluationCommand("remember this"), undefined);
});
