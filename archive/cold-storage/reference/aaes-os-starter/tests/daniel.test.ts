import { strict as assert } from "node:assert"
import { DanielModule } from "../src/modules/daniel/executor.js"
import { AAESAction } from "../src/core/action.js"
import { AAESContext } from "../src/core/context.js"
import { AAESRequest } from "../src/core/request.js"

(async () => {
  const mod = new DanielModule()
  const action: AAESAction = {
    actionId: "act_1",
    target: "render",
    parameters: { scene: "test" }
  }
  const req: AAESRequest = {
    id: "req_1",
    actorId: "actor_1",
    timestamp: new Date().toISOString(),
    channel: "test",
    payload: {},
    scope: { name: "test" }
  }
  const ctx: AAESContext = {
    request: req,
    traceId: "trace_req_1",
    session: {},
    policies: { name: "default", rules: [] }
  }

  assert.equal(mod.canHandle(action), true)
  const result = await mod.execute(action, ctx)
  assert.equal(result.status, "success")
  assert.equal(result.actionId, "act_1")
})()
