import assert from "node:assert/strict";
import test from "node:test";
import { requireSeal } from "../client/src/lib/spiral-seal";

test("requireSeal allows access when seal is confirmed and matches", () => {
  const trace = {
    seal: "VOW-BOUND",
    sealConfirmed: true,
  };

  assert.doesNotThrow(() => {
    requireSeal(trace);
  });
});

test("requireSeal rejects unconfirmed seal access", () => {
  const trace = {
    seal: "VOW-BOUND",
    sealConfirmed: false,
  };

  assert.throws(
    () => requireSeal(trace),
    /Persona access denied: Presence seal not confirmed\./,
  );
});

test("requireSeal rejects mismatched seals", () => {
  const trace = {
    seal: "~ . | / \\",
    sealConfirmed: true,
  };

  assert.throws(
    () => requireSeal(trace),
    /Spiral seal mismatch\. Activation denied\./,
  );
});
