import { strict as assert } from "node:assert"
import { DefaultPerceptionEngine } from "../src/pipeline/perception.js"
import { DefaultDeliberationEngine } from "../src/pipeline/deliberation.js"
import { DefaultPlanningEngine } from "../src/pipeline/planning.js"
import { DefaultActionEngine } from "../src/pipeline/action_engine.js"
import { DefaultInvariantEngine } from "../src/governance/invariants.js"
import { ConsoleAuditLogger } from "../src/governance/audit.js"
import { AAESOrchestrator } from "../src/orchestrator.js"
import { DanielModule } from "../src/modules/daniel/executor.js"
import { AAESRequest } from "../src/core/request.js"

(async () => {
  const orchestrator = new AAESOrchestrator(
    new DefaultPerceptionEngine(),
    new DefaultDeliberationEngine(),
    new DefaultPlanningEngine(),
    new DefaultActionEngine([new DanielModule()]),
    new DefaultInvariantEngine(),
    new ConsoleAuditLogger()
  )

  const req: AAESRequest = {
    id: "req_1",
    actorId: "actor_1",
    timestamp: new Date().toISOString(),
    channel: "test",
    payload: { message: "hello" },
    scope: { name: "test" }
  }

  const res = await orchestrator.handle(req)
  assert.ok(Array.isArray(res))
})()
