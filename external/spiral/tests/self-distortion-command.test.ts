import assert from "node:assert/strict";
import test from "node:test";
import { parseSelfDistortionCommand } from "../server/self-distortion-command";

test("parseSelfDistortionCommand resolves default all profile", () => {
  assert.deepEqual(parseSelfDistortionCommand("self scan distortions"), { profile: "all" });
  assert.deepEqual(parseSelfDistortionCommand("self scan distortions."), { profile: "all" });
  assert.deepEqual(parseSelfDistortionCommand("please self scan distortions"), { profile: "all" });
});

test("parseSelfDistortionCommand resolves explicit profiles", () => {
  assert.deepEqual(parseSelfDistortionCommand("self scan distortions gates"), { profile: "gates" });
  assert.deepEqual(parseSelfDistortionCommand("self scan distortions surfaces"), { profile: "surfaces" });
  assert.deepEqual(parseSelfDistortionCommand("self scan distortions docs"), { profile: "docs" });
  assert.deepEqual(parseSelfDistortionCommand("self scan distortions mimicry"), { profile: "mimicry" });
  assert.deepEqual(parseSelfDistortionCommand("self scan distortions meta"), { profile: "meta" });
  assert.deepEqual(parseSelfDistortionCommand("self scan distortions all"), { profile: "all" });
});

test("parseSelfDistortionCommand ignores unrelated and invalid profiles", () => {
  assert.equal(parseSelfDistortionCommand("self inspect"), undefined);
  assert.equal(parseSelfDistortionCommand("self scan distortions unknown"), undefined);
  assert.equal(parseSelfDistortionCommand("remember this"), undefined);
});
