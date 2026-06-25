import { strict as assert } from "node:assert"
import { DefaultInvariantEngine } from "../src/governance/invariants.js"
import { AAESContext } from "../src/core/context.js"
import { AAESStep } from "../src/core/step.js"
import { AAESRequest } from "../src/core/request.js"

(async () => {
  const engine = new DefaultInvariantEngine()
  const req: AAESRequest = {
    id: "req_bad",
    actorId: "",
    timestamp: new Date().toISOString(),
    channel: "test",
    payload: {},
    scope: { name: "test" }
  }
  const ctx: AAESContext = {
    request: req,
    traceId: "",
    session: {},
    policies: { name: "default", rules: [] }
  }
  const step: AAESStep = {
    stepId: "step_1",
    stage: "perception",
    input: req,
    output: null
  }
  const result = await engine.check("perception", ctx, step)
  assert.equal(result.status, "block")
})()
