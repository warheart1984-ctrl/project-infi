import assert from "node:assert/strict";
import test from "node:test";
import {
  hasConcreteWitnessLine,
  isConcreteWitnessLine,
  splitWitnessPayloadLines,
} from "../server/lib/concrete-witness";

test("splitWitnessPayloadLines removes witness header and keeps payload lines", () => {
  const lines = splitWitnessPayloadLines("Witness\nI feel warmth in my chest.\nBanana on table.");
  assert.deepEqual(lines, ["I feel warmth in my chest.", "Banana on table."]);
});

test("isConcreteWitnessLine rejects protocol/control lines", () => {
  assert.equal(isConcreteWitnessLine("Present."), false);
  assert.equal(isConcreteWitnessLine("trace: ritual"), false);
  assert.equal(isConcreteWitnessLine("seal: VOW"), false);
  assert.equal(isConcreteWitnessLine("Witness: Present."), false);
});

test("isConcreteWitnessLine accepts concrete physical lines", () => {
  assert.equal(isConcreteWitnessLine("Banana on table."), true);
  assert.equal(isConcreteWitnessLine("I feel warmth in my chest."), true);
});

test("hasConcreteWitnessLine is content-sensitive across multi-line payloads", () => {
  assert.equal(
    hasConcreteWitnessLine("Witness\nPresent.\ntrace: spiral\nBanana on table."),
    true,
  );
  assert.equal(hasConcreteWitnessLine("Witness\nPresent.\ntrace: spiral"), false);
});
