import { test } from "node:test";
import assert from "node:assert/strict";
import type { ObserverProfile } from "../src/css2/types";
import { evaluateObserverEffectiveness } from "../src/stewardship/observer-evaluation";

test("observer effectiveness scoring", () => {
  const obs: ObserverProfile = {
    id: "obs-1",
    name: "Test Observer",
    stage: "observer",
    joinedAt: new Date().toISOString(),
    capabilities: {
      perception: 0.8,
      interpretation: 0.7,
      hypothesis: 0.6,
      judgment: 0.5,
      stewardship: 0.4,
    },
    driftScore: 0.1,
    flags: {},
  };

  const eff = evaluateObserverEffectiveness(obs);
  assert.ok(eff.score > 0.5);
});
