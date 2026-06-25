import test from "node:test";
import assert from "node:assert/strict";
import { validateCAA1 } from "../../../crk1/receipts/caa1.js";

test("rejects continuity_passed when delta < threshold", () => {
  const receipt = {
    cxd_id: "1",
    timestamp: new Date().toISOString(),
    steward_id: "S2",
    isolation_proof: "a".repeat(64),
    lineage_used: { crr_hash: "b".repeat(64), clg_hash: "c".repeat(64) },
    pre_assimilation_judgment: "d".repeat(64),
    post_assimilation_judgment: "e".repeat(64),
    assimilation_delta: 0.01,
    assimilation_threshold: 0.1,
    continuity_passed: true,
    proof_bundle: "f".repeat(64),
  };

  assert.throws(() => validateCAA1(receipt));
});
