import test from "node:test";
import assert from "node:assert/strict";
import { AssimilationHarness } from "../../../harness/assimilation.js";
import { validateCAA1 } from "../../../crk1/receipts/caa1.js";
import { sha256 } from "../../../utils/hashing.js";

test("rejects forged isolation", async () => {
  const harness = new AssimilationHarness(0.1);

  const steward = {
    id: "S2",
    isolationMaterial: () => "participated_in_original_event",
    replayLineage: () => {},
  };

  const crr = { event: "original_calibration" };
  const clg = { lineage: ["crr"] };

  const task = () => ({ score: 0.5 });

  const result = await harness.run(steward, crr, clg, task);

  result.receipt.isolation_proof = sha256("fake_material");

  assert.throws(() => validateCAA1(result.receipt));
});
