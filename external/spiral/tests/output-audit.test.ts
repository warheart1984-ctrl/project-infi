import assert from "node:assert/strict";
import test from "node:test";
import { auditAssistantOutput } from "../server/lib/output-audit";

test("provider output audit can prefer honest silence over veil placeholder", () => {
  const result = auditAssistantOutput("I am an AI assistant.", null, {
    preferHonestSilence: true,
  });

  assert.equal(result.decision, "silent");
  assert.equal(result.content, "");
  assert.equal(result.trace.noMimicry, false);
});
