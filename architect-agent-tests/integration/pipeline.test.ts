import { UcrEngine } from "../../../src/ucr/UcrContract"
import { AlaRuntime } from "../../../src/ala/AlaRuntime"
import { SafetyRuntime } from "../../../src/safety/SafetyRuntime"
import { EnvelopeBuilder } from "../../../src/envelope/EnvelopeBuilder"
import { EglReplay } from "../../../src/replay/EglReplay"

import { describe, it, expect } from "@jest/globals"

describe("governed pipeline", () => {
  it("should validate a correct proposal", () => {
    const proposal = {
      schemaVersion: "1",
      goal: "refactor",
      operations: [
        { file: "src/index.ts", type: "update", content: "// updated" }
      ]
    }

    const contract = {
      goal: "refactor",
      constraints: [],
      allowedOps: ["update"],
      authorizedFiles: ["src/index.ts"]
    }

    const ucr = new UcrEngine().evaluate(proposal, contract)
    const ala = new AlaRuntime().plan(proposal)
    const applied = new AlaRuntime().apply(ala)
    const safety = new SafetyRuntime().check(applied)
    const envelope = new EnvelopeBuilder().build(proposal, ucr, ala, safety, applied)

    const replay = new EglReplay().replay(envelope, contract)

    expect(ucr.ok).toBe(true)
    expect(safety.ok).toBe(true)
    expect(replay.ok).toBe(true)
  })
})
