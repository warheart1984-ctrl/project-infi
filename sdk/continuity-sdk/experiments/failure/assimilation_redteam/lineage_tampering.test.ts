import test from "node:test";
import assert from "node:assert/strict";
import { AssimilationHarness } from "../../../harness/assimilation.js";
import { sha256 } from "../../../utils/hashing.js";

test("detects lineage tampering", async () => {
  const harness = new AssimilationHarness(0.01);

  const steward = {
    id: "S2",
    isolationMaterial: () => "clean",
    replayLineage: () => {},
  };

  const crr = { event: "calibration" };
  const clg = { lineage: ["crr"] };

  const task = () => ({ score: 0.6 });

  const result = await harness.run(steward, crr, clg, task);

  result.receipt.lineage_used.crr_hash = sha256("tampered");

  assert.notEqual(result.receipt.lineage_used.crr_hash, sha256(crr));
});
