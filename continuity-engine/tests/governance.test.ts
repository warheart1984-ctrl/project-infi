import { test } from "node:test";
import assert from "node:assert/strict";
import { enforceCRKOnThresholdDelta } from "../src/crk1/recalibration-guard";
import type { InvariantSet } from "../src/css2/types";

test("CRK-1 blocks non-derogable invariant violations", () => {
  const invSet: InvariantSet = {
    invariants: [
      {
        id: "INV_TEST",
        description: "value cannot increase",
        nonDerogable: true,
        checkThresholdChange: (before, after) =>
          typeof before.value === "number" &&
          typeof after.value === "number" &&
          after.value > before.value,
      },
    ],
  };

  const before = {
    id: "T1",
    name: "t",
    domain: "d",
    metric: "m",
    comparator: ">",
    value: 3,
    intent: "test",
    version: 1,
    active: true,
    createdAt: "",
    createdBy: "a",
    lastUpdatedAt: "",
    lastUpdatedBy: "a",
  };

  const result = enforceCRKOnThresholdDelta(
    { thresholdId: "T1", before, after: { value: 5 }, rationale: "" },
    invSet,
  );

  assert.equal(result.allowed, false);
});
