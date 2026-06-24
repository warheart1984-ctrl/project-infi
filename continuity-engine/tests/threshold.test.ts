import { test } from "node:test";
import assert from "node:assert/strict";
import type { Threshold, ThresholdDelta } from "../src/css2/types";
import { InMemoryThresholdRegistry } from "../src/registry/memory-threshold-registry";

test("threshold creation + delta application", async () => {
  const registry = new InMemoryThresholdRegistry();

  const th: Threshold = await registry.create({
    id: "T1",
    name: "incident_rate",
    domain: "Org.incident",
    metric: "incidents_per_24h",
    comparator: ">",
    value: 3,
    intent: "trigger escalation",
    createdBy: "observer-1",
  });

  assert.equal(th.version, 1);

  const delta: ThresholdDelta = {
    thresholdId: "T1",
    before: th,
    after: { value: 2 },
    rationale: "late interventions",
  };

  const updated = await registry.applyDelta(delta, "observer-2");
  assert.equal(updated.value, 2);
  assert.equal(updated.version, 2);
});
